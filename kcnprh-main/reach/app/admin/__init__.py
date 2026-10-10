from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort, jsonify
from hashlib import md5
from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload
from ..models import Admin, Post, Category, SubCategory, Page, Comment, get_visitor_count, set_visitor_count
from .. import db
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask import current_app
import os
import uuid
from PIL import Image
import bleach
from urllib.parse import urlparse

bp = Blueprint("admin", __name__, template_folder="../templates/admin")

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_FEATURED_IMAGE_SIZE = (1600, 1000)
FACEBOOK_EMBED_HOSTS = {"www.facebook.com", "web.facebook.com", "facebook.com"}
FACEBOOK_EMBED_PATHS = {"/plugins/post.php", "/plugins/video.php"}
POST_DETAIL_TAGS = [
    "p", "br", "strong", "em", "u", "ul", "ol", "li",
    "blockquote", "a", "h1", "h2", "h3", "h4", "img",
    "code", "pre", "span", "div", "iframe",
]
IFRAME_ATTRIBUTES = {
    "src", "title", "width", "height", "allow", "allowfullscreen",
    "frameborder", "scrolling", "loading", "referrerpolicy",
}


def post_detail_attribute_filter(tag: str, name: str, value: str) -> bool:
    if tag == "a":
        return name in {"href", "title", "rel", "target"}
    if tag == "img":
        return name in {"src", "alt", "title"}
    if tag == "span":
        return name == "style"
    if tag == "div":
        return name == "class" and any(c in {"facebook-post-embed", "facebook-video-embed", "fb-post-embed", "post-gallery-grid", "single-image", "two-images", "multi-images"} for c in value.split())
    if tag == "iframe":
        if name == "src":
            parsed = urlparse(value)
            return (
                parsed.scheme == "https"
                and parsed.netloc.lower() in FACEBOOK_EMBED_HOSTS
                and parsed.path in FACEBOOK_EMBED_PATHS
            )
        return name in IFRAME_ATTRIBUTES
    return False


def clean_post_details(details: str) -> str:
    return bleach.clean(
        details,
        tags=POST_DETAIL_TAGS,
        attributes=post_detail_attribute_filter,
        protocols=["http", "https", "mailto"],
        strip=True,
    )


def next_id(column):
    return (db.session.query(func.max(column)).scalar() or 0) + 1


def compact_post_ids():
    post_ids = [row[0] for row in db.session.query(Post.id).order_by(Post.id).all()]
    id_map = {old_id: new_id for new_id, old_id in enumerate(post_ids, start=1) if old_id != new_id}
    if not id_map:
        return

    for old_id, new_id in id_map.items():
        Post.query.filter(Post.id == old_id).update({Post.id: -new_id}, synchronize_session=False)
        Comment.query.filter(Comment.postId == old_id).update({Comment.postId: -new_id}, synchronize_session=False)

    db.session.flush()

    for old_id, new_id in id_map.items():
        Post.query.filter(Post.id == -new_id).update({Post.id: new_id}, synchronize_session=False)
        Comment.query.filter(Comment.postId == -new_id).update({Comment.postId: new_id}, synchronize_session=False)


def upload_dir() -> str:
    return current_app.config.get("UPLOAD_FOLDER") or os.path.join(current_app.static_folder, "uploads")


def upload_path(filename: str) -> str:
    return os.path.join(upload_dir(), os.path.basename(filename))


def delete_uploaded_image(filename: str | None) -> None:
    if not filename:
        return
    path = upload_path(filename)
    try:
        if os.path.isfile(path):
            os.remove(path)
    except OSError:
        current_app.logger.warning("Failed to delete uploaded image: %s", filename)


def save_featured_image(image_file) -> str:
    allowed_ext = ALLOWED_IMAGE_EXTENSIONS
    base = secure_filename(image_file.filename or "")
    name, ext = os.path.splitext(base)
    ext = ext.lower()
    if ext not in allowed_ext:
        raise ValueError("Unsupported image type. Use JPG, PNG, or WEBP.")

    unique_name = f"{name}_{uuid.uuid4().hex[:8]}{ext}"
    os.makedirs(upload_dir(), exist_ok=True)
    image_path = upload_path(unique_name)

    try:
        image_file.stream.seek(0)
        with Image.open(image_file.stream) as image:
            image.verify()

        image_file.stream.seek(0)
        with Image.open(image_file.stream) as image:
            image.thumbnail(MAX_FEATURED_IMAGE_SIZE)
            save_kwargs = {"optimize": True}

            if ext in {".jpg", ".jpeg"}:
                image = image.convert("RGB")
                save_kwargs["quality"] = 85
                image.save(image_path, format="JPEG", **save_kwargs)
            elif ext == ".webp":
                save_kwargs["quality"] = 85
                image.save(image_path, format="WEBP", **save_kwargs)
            else:
                image.save(image_path, format="PNG", **save_kwargs)
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("Uploaded file is not a valid image.") from exc

    return unique_name


def login_required(view):
    from functools import wraps

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not session.get("admin_username"):
            return redirect(url_for("admin.login"))
        return view(*args, **kwargs)
    return wrapper


@bp.get("/")
@login_required
def dashboard():
    stats = {
        "posts": db.session.query(func.count(Post.id)).scalar() or 0,
        "categories": db.session.query(func.count(Category.id)).scalar() or 0,
        "subcategories": db.session.query(func.count(SubCategory.SubCategoryId)).scalar() or 0,
        "pages": db.session.query(func.count(Page.id)).scalar() or 0,
        "comments_pending": db.session.query(func.count(Comment.id)).filter(Comment.status == 0).scalar() or 0,
        "visitor_count": get_visitor_count(),
    }
    return render_template("admin/dashboard.html", stats=stats)


@bp.post("/settings/visitor-count")
@login_required
def update_visitor_count():
    new_count = request.form.get("visitor_count", type=int)
    if new_count is not None and new_count >= 0:
        set_visitor_count(new_count)
        flash(f"Visitor counter updated to {new_count:,}", "success")
    else:
        flash("Invalid visitor count number.", "danger")
    return redirect(url_for("admin.dashboard"))


from .. import limiter


@bp.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute", methods=["POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        admin = Admin.query.filter_by(AdminUserName=username).first()
        if not admin:
            flash("Invalid credentials", "danger")
            return render_template("admin/login.html")
        stored = (admin.AdminPassword or "").strip()
        ok = False
        # If stored is a modern Werkzeug hash (e.g., scrypt, pbkdf2, etc.), verify with check_password_hash
        if ":" in stored and not (len(stored) == 32 and all(c in "0123456789abcdefABCDEF" for c in stored)):
            # Supports schemes like "scrypt:...", "pbkdf2:...", etc.
            ok = check_password_hash(stored, password)
        # If stored looks like legacy MD5 (32 hex), check MD5(password) and upgrade to PBKDF2
        elif len(stored) == 32 and all(c in "0123456789abcdefABCDEF" for c in stored):
            if md5(password.encode("utf-8")).hexdigest().lower() == stored.lower():
                ok = True
                # upgrade hash to PBKDF2 for better security
                admin.AdminPassword = generate_password_hash(password)
                db.session.commit()
        if ok:
            session["admin_username"] = admin.AdminUserName
            flash("Logged in", "success")
            return redirect(url_for("admin.dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("admin/login.html")


@bp.get("/logout")
def logout():
    session.pop("admin_username", None)
    flash("Logged out", "success")
    return redirect(url_for("admin.login"))


# Posts CRUD
@bp.get("/posts")
@login_required
def posts_list():
    q = (request.args.get("q") or "").strip()
    category_id = request.args.get("category_id", type=int)
    subcategory_id = request.args.get("subcategory_id", type=int)
    status = (request.args.get("status") or "").strip()

    query = Post.query.options(
        selectinload(Post.category),
        selectinload(Post.subcategory),
        selectinload(Post.author),
    )
    if q:
        pattern = f"%{q}%"
        query = query.filter(or_(Post.PostTitle.ilike(pattern), Post.PostDetails.ilike(pattern)))
    if category_id:
        query = query.filter(Post.CategoryId == category_id)
    if subcategory_id:
        query = query.filter(Post.SubCategoryId == subcategory_id)
    if status in {"1", "0"}:
        query = query.filter(Post.Is_Active == int(status))

    posts = query.order_by(Post.id.asc()).all()
    filters = {
        "q": q,
        "category_id": category_id,
        "subcategory_id": subcategory_id,
        "status": status,
        "active": bool(q or category_id or subcategory_id or status in {"1", "0"}),
    }
    categories = Category.query.order_by(Category.CategoryName).all()
    subcategories = SubCategory.query.order_by(SubCategory.Subcategory).all()
    return render_template(
        "admin/posts_list.html",
        posts=posts,
        categories=categories,
        subcategories=subcategories,
        filters=filters,
    )


@bp.route("/posts/new", methods=["GET", "POST"])
@login_required
def posts_create():
    if request.method == "POST":
        compact_post_ids()
        title = request.form.get("PostTitle", "")
        category_id = request.form.get("CategoryId", type=int)
        subcategory_id = request.form.get("SubCategoryId", type=int)
        details = request.form.get("PostDetails", "")
        details = clean_post_details(details)
        is_active = 1 if request.form.get("Is_Active") == "1" else 0
        image_file = request.files.get("PostImage")
        filename = None
        if image_file and image_file.filename:
            try:
                filename = save_featured_image(image_file)
            except ValueError as exc:
                flash(str(exc), "danger")
                return render_template("admin/post_form.html", categories=Category.query.order_by(Category.CategoryName).all(), subcategories=SubCategory.query.order_by(SubCategory.Subcategory).all(), post=None)
        kwargs = dict(
            id=next_id(Post.id),
            PostTitle=title,
            CategoryId=category_id,
            SubCategoryId=subcategory_id,
            PostDetails=details,
            Is_Active=is_active,
            viewCounter=0,
            postedBy=session.get("admin_username"),
        )
        if filename and hasattr(Post, 'PostImage'):
            kwargs['PostImage'] = filename
        post = Post(**kwargs)
        db.session.add(post)
        db.session.commit()
        flash("Post created", "success")
        return redirect(url_for("admin.posts_list"))
    categories = Category.query.order_by(Category.CategoryName).all()
    subcategories = SubCategory.query.order_by(SubCategory.Subcategory).all()
    return render_template("admin/post_form.html", categories=categories, subcategories=subcategories, post=None)


@bp.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
@login_required
def posts_edit(post_id: int):
    post = Post.query.get_or_404(post_id)
    if request.method == "POST":
        post.PostTitle = request.form.get("PostTitle", post.PostTitle)
        post.CategoryId = request.form.get("CategoryId", type=int)
        post.SubCategoryId = request.form.get("SubCategoryId", type=int)
        details = request.form.get("PostDetails", post.PostDetails)
        post.PostDetails = clean_post_details(details)
        post.Is_Active = 1 if request.form.get("Is_Active") == "1" else 0
        post.lastUpdatedBy = session.get("admin_username")
        image_file = request.files.get("PostImage")
        old_image = post.PostImage
        if image_file and image_file.filename:
            try:
                unique_name = save_featured_image(image_file)
            except ValueError as exc:
                flash(str(exc), "danger")
                return render_template("admin/post_form.html", categories=Category.query.order_by(Category.CategoryName).all(), subcategories=SubCategory.query.order_by(SubCategory.Subcategory).all(), post=post)
            if hasattr(post, 'PostImage'):
                post.PostImage = unique_name
            delete_uploaded_image(old_image)
        elif request.form.get("RemovePostImage") == "1":
            if hasattr(post, "PostImage"):
                post.PostImage = None
            delete_uploaded_image(old_image)
        db.session.commit()
        flash("Post updated", "success")
        return redirect(url_for("admin.posts_list"))
    categories = Category.query.order_by(Category.CategoryName).all()
    subcategories = SubCategory.query.order_by(SubCategory.Subcategory).all()
    return render_template("admin/post_form.html", categories=categories, subcategories=subcategories, post=post)


@bp.post("/posts/<int:post_id>/delete")
@login_required
def posts_delete(post_id: int):
    post = Post.query.get_or_404(post_id)
    old_image = post.PostImage
    db.session.delete(post)
    db.session.flush()
    compact_post_ids()
    db.session.commit()
    delete_uploaded_image(old_image)
    flash("Post deleted", "success")
    return redirect(url_for("admin.posts_list"))


# Editor asset uploads (Quill image upload)
@bp.post("/posts/upload-image")
@login_required
def posts_upload_image():
    image_file = request.files.get("image")
    if not image_file or not image_file.filename:
        return jsonify({"error": "No image provided"}), 400
    try:
        unique_name = save_featured_image(image_file)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 415

    url = url_for("static", filename=f"uploads/{unique_name}")
    return jsonify({"url": url}), 200


# Categories CRUD
@bp.get("/categories")
@login_required
def categories_list():
    categories = Category.query.order_by(Category.CategoryName).all()
    return render_template("admin/categories_list.html", categories=categories)


@bp.route("/categories/new", methods=["GET", "POST"])
@login_required
def categories_create():
    if request.method == "POST":
        name = request.form.get("CategoryName", "")
        desc = request.form.get("Description", "")
        is_active = 1 if request.form.get("Is_Active") == "1" else 0
        cat = Category(id=next_id(Category.id), CategoryName=name, Description=desc, Is_Active=is_active)
        db.session.add(cat)
        db.session.commit()
        flash("Category created", "success")
        return redirect(url_for("admin.categories_list"))
    return render_template("admin/category_form.html", category=None)


@bp.route("/categories/<int:category_id>/edit", methods=["GET", "POST"])
@login_required
def categories_edit(category_id: int):
    category = Category.query.get_or_404(category_id)
    if request.method == "POST":
        category.CategoryName = request.form.get("CategoryName", category.CategoryName)
        category.Description = request.form.get("Description", category.Description)
        category.Is_Active = 1 if request.form.get("Is_Active") == "1" else 0
        db.session.commit()
        flash("Category updated", "success")
        return redirect(url_for("admin.categories_list"))
    return render_template("admin/category_form.html", category=category)


@bp.post("/categories/<int:category_id>/delete")
@login_required
def categories_delete(category_id: int):
    category = Category.query.get_or_404(category_id)
    db.session.delete(category)
    db.session.commit()
    flash("Category deleted", "success")
    return redirect(url_for("admin.categories_list"))


# SubCategories CRUD
@bp.get("/subcategories")
@login_required
def subcategories_list():
    subs = (
        SubCategory.query.options(selectinload(SubCategory.category))
        .order_by(SubCategory.Subcategory)
        .all()
    )
    return render_template("admin/subcategories_list.html", subcategories=subs)


@bp.route("/subcategories/new", methods=["GET", "POST"])
@login_required
def subcategories_create():
    if request.method == "POST":
        name = request.form.get("Subcategory", "")
        desc = request.form.get("SubCatDescription", "")
        category_id = request.form.get("CategoryId", type=int)
        is_active = 1 if request.form.get("Is_Active") == "1" else 0
        sub = SubCategory(
            SubCategoryId=next_id(SubCategory.SubCategoryId),
            Subcategory=name,
            SubCatDescription=desc,
            CategoryId=category_id,
            Is_Active=is_active,
        )
        db.session.add(sub)
        db.session.commit()
        flash("SubCategory created", "success")
        return redirect(url_for("admin.subcategories_list"))
    categories = Category.query.order_by(Category.CategoryName).all()
    return render_template("admin/subcategory_form.html", subcategory=None, categories=categories)


@bp.route("/subcategories/<int:sub_id>/edit", methods=["GET", "POST"])
@login_required
def subcategories_edit(sub_id: int):
    sub = SubCategory.query.get_or_404(sub_id)
    if request.method == "POST":
        sub.Subcategory = request.form.get("Subcategory", sub.Subcategory)
        sub.SubCatDescription = request.form.get("SubCatDescription", sub.SubCatDescription)
        sub.CategoryId = request.form.get("CategoryId", type=int)
        sub.Is_Active = 1 if request.form.get("Is_Active") == "1" else 0
        db.session.commit()
        flash("SubCategory updated", "success")
        return redirect(url_for("admin.subcategories_list"))
    categories = Category.query.order_by(Category.CategoryName).all()
    return render_template("admin/subcategory_form.html", subcategory=sub, categories=categories)


@bp.post("/subcategories/<int:sub_id>/delete")
@login_required
def subcategories_delete(sub_id: int):
    sub = SubCategory.query.get_or_404(sub_id)
    db.session.delete(sub)
    db.session.commit()
    flash("SubCategory deleted", "success")
    return redirect(url_for("admin.subcategories_list"))


# Pages CRUD
@bp.get("/pages")
@login_required
def pages_list():
    pages = Page.query.order_by(Page.PageName).all()
    return render_template("admin/pages_list.html", pages=pages)


@bp.route("/pages/new", methods=["GET", "POST"])
@login_required
def pages_create():
    if request.method == "POST":
        name = request.form.get("PageName", "")
        title = request.form.get("PageTitle", "")
        desc = request.form.get("Description", "")
        pg = Page(id=next_id(Page.id), PageName=name, PageTitle=title, Description=desc)
        db.session.add(pg)
        db.session.commit()
        flash("Page created", "success")
        return redirect(url_for("admin.pages_list"))
    return render_template("admin/page_form.html", page=None)


@bp.route("/pages/<int:page_id>/edit", methods=["GET", "POST"])
@login_required
def pages_edit(page_id: int):
    pg = Page.query.get_or_404(page_id)
    if request.method == "POST":
        pg.PageName = request.form.get("PageName", pg.PageName)
        pg.PageTitle = request.form.get("PageTitle", pg.PageTitle)
        pg.Description = request.form.get("Description", pg.Description)
        db.session.commit()
        flash("Page updated", "success")
        return redirect(url_for("admin.pages_list"))
    return render_template("admin/page_form.html", page=pg)


@bp.post("/pages/<int:page_id>/delete")
@login_required
def pages_delete(page_id: int):
    pg = Page.query.get_or_404(page_id)
    db.session.delete(pg)
    db.session.commit()
    flash("Page deleted", "success")
    return redirect(url_for("admin.pages_list"))


# Comment moderation
@bp.get("/comments")
@login_required
def comments_list():
    comments = (
        Comment.query.options(selectinload(Comment.post))
        .order_by(Comment.postingDate.desc())
        .all()
    )
    return render_template("admin/comments_list.html", comments=comments)


# Admin user management
@bp.get("/users")
@login_required
def users_list():
    users = Admin.query.order_by(Admin.AdminUserName).all()
    return render_template("admin/users_list.html", users=users)


@bp.route("/users/new", methods=["GET", "POST"])
@login_required
def users_create():
    if request.method == "POST":
        username = request.form.get("AdminUserName", "").strip()
        email = request.form.get("AdminEmailId", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Username and password are required", "danger")
            return render_template("admin/user_form.html", user=None)
        # Basic password policy: min 8 chars, must include letters and numbers
        if len(password) < 8 or password.isalpha() or password.isdigit():
            flash("Password must be at least 8 characters and include letters and numbers.", "danger")
            return render_template("admin/user_form.html", user=None)
        if Admin.query.filter_by(AdminUserName=username).first():
            flash("Username already exists", "danger")
            return render_template("admin/user_form.html", user=None)
        hashed = generate_password_hash(password)  # pbkdf2:sha256
        user = Admin(
            id=next_id(Admin.id),
            AdminUserName=username,
            AdminEmailId=email,
            AdminPassword=hashed,
            userType=1,
        )
        db.session.add(user)
        db.session.commit()
        flash("Admin user created", "success")
        return redirect(url_for("admin.users_list"))
    return render_template("admin/user_form.html", user=None)


@bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def users_edit(user_id: int):
    user = Admin.query.get_or_404(user_id)
    if request.method == "POST":
        user.AdminEmailId = request.form.get("AdminEmailId", user.AdminEmailId)
        user.userType = request.form.get("userType", type=int) or user.userType
        db.session.commit()
        flash("Admin user updated", "success")
        return redirect(url_for("admin.users_list"))
    return render_template("admin/user_form.html", user=user)


@bp.route("/users/<int:user_id>/password", methods=["POST"])
@login_required
def users_change_password(user_id: int):
    user = Admin.query.get_or_404(user_id)
    password = request.form.get("password", "")
    confirm = request.form.get("confirm", "")
    if not password or password != confirm:
        flash("Passwords do not match", "danger")
        return redirect(url_for("admin.users_edit", user_id=user_id))
    if len(password) < 8 or password.isalpha() or password.isdigit():
        flash("Password must be at least 8 characters and include letters and numbers.", "danger")
        return redirect(url_for("admin.users_edit", user_id=user_id))
    user.AdminPassword = generate_password_hash(password)
    db.session.commit()
    flash("Password updated", "success")
    return redirect(url_for("admin.users_list"))


@bp.post("/comments/<int:comment_id>/approve")
@login_required
def comments_approve(comment_id: int):
    c = Comment.query.get_or_404(comment_id)
    c.status = 1
    db.session.commit()
    flash("Comment approved", "success")
    return redirect(url_for("admin.comments_list"))


@bp.post("/comments/<int:comment_id>/reject")
@login_required
def comments_reject(comment_id: int):
    c = Comment.query.get_or_404(comment_id)
    c.status = 2  # mark as rejected
    db.session.commit()
    flash("Comment rejected", "success")
    return redirect(url_for("admin.comments_list"))
