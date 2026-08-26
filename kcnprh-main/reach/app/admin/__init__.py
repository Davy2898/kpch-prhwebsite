from flask import Blueprint, render_template, request, redirect, url_for, flash, session, abort, jsonify
from hashlib import md5
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from ..models import Admin, Post, Category, SubCategory, Page, Comment
from .. import db
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from flask import current_app
import os
import uuid
import io
from PIL import Image
import bleach

bp = Blueprint("admin", __name__, template_folder="../templates/admin")


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
    }
    return render_template("admin/dashboard.html", stats=stats)


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
    posts = (
        Post.query.options(
            selectinload(Post.category),
            selectinload(Post.subcategory),
            selectinload(Post.author),
        )
        .order_by(Post.PostingDate.desc())
        .all()
    )
    return render_template("admin/posts_list.html", posts=posts)


@bp.route("/posts/new", methods=["GET", "POST"])
@login_required
def posts_create():
    if request.method == "POST":
        title = request.form.get("PostTitle", "")
        category_id = request.form.get("CategoryId", type=int)
        subcategory_id = request.form.get("SubCategoryId", type=int)
        details = request.form.get("PostDetails", "")
        # Sanitize HTML to prevent XSS
        details = bleach.clean(
            details,
            tags=[
                "p", "br", "strong", "em", "u", "ul", "ol", "li",
                "blockquote", "a", "h1", "h2", "h3", "h4", "img",
                "code", "pre", "span"
            ],
            attributes={
                "a": ["href", "title", "rel", "target"],
                "img": ["src", "alt", "title"],
                "span": ["style"],
            },
            protocols=["http", "https", "mailto", "data"],
            strip=True,
        )
        is_active = 1 if request.form.get("Is_Active") == "1" else 0
        image_file = request.files.get("PostImage")
        filename = None
        if image_file and image_file.filename:
            # Validate and generate a unique safe filename
            allowed_ext = {".jpg", ".jpeg", ".png", ".webp"}
            base = secure_filename(image_file.filename)
            name, ext = os.path.splitext(base)
            if ext.lower() not in allowed_ext:
                flash("Unsupported image type. Use JPG, PNG, or WEBP.", "danger")
                return render_template("admin/post_form.html", categories=Category.query.order_by(Category.CategoryName).all(), subcategories=SubCategory.query.order_by(SubCategory.Subcategory).all(), post=None)
            # Magic-byte validation using Pillow
            try:
                image_file.stream.seek(0)
                with Image.open(image_file.stream) as im:
                    im.verify()
                image_file.stream.seek(0)
            except Exception:
                flash("Uploaded file is not a valid image.", "danger")
                return render_template("admin/post_form.html", categories=Category.query.order_by(Category.CategoryName).all(), subcategories=SubCategory.query.order_by(SubCategory.Subcategory).all(), post=None)
            unique_name = f"{name}_{uuid.uuid4().hex[:8]}{ext.lower()}"
            upload_dir = current_app.config.get("UPLOAD_FOLDER") or os.path.join(current_app.static_folder, 'uploads')
            os.makedirs(upload_dir, exist_ok=True)
            image_path = os.path.join(upload_dir, unique_name)
            try:
                image_file.save(image_path)
            except Exception:
                flash("Failed to save image.", "danger")
                return render_template("admin/post_form.html", categories=Category.query.order_by(Category.CategoryName).all(), subcategories=SubCategory.query.order_by(SubCategory.Subcategory).all(), post=None)
            filename = unique_name
        kwargs = dict(PostTitle=title, CategoryId=category_id, SubCategoryId=subcategory_id, PostDetails=details, Is_Active=is_active, postedBy=session.get("admin_username"))
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
        post.PostDetails = bleach.clean(
            details,
            tags=[
                "p", "br", "strong", "em", "u", "ul", "ol", "li",
                "blockquote", "a", "h1", "h2", "h3", "h4", "img",
                "code", "pre", "span"
            ],
            attributes={
                "a": ["href", "title", "rel", "target"],
                "img": ["src", "alt", "title"],
                "span": ["style"],
            },
            protocols=["http", "https", "mailto", "data"],
            strip=True,
        )
        post.Is_Active = 1 if request.form.get("Is_Active") == "1" else 0
        post.lastUpdatedBy = session.get("admin_username")
        image_file = request.files.get("PostImage")
        if image_file and image_file.filename:
            allowed_ext = {".jpg", ".jpeg", ".png", ".webp"}
            base = secure_filename(image_file.filename)
            name, ext = os.path.splitext(base)
            if ext.lower() not in allowed_ext:
                flash("Unsupported image type. Use JPG, PNG, or WEBP.", "danger")
                return render_template("admin/post_form.html", categories=Category.query.order_by(Category.CategoryName).all(), subcategories=SubCategory.query.order_by(SubCategory.Subcategory).all(), post=post)
            # Magic-byte validation using Pillow
            try:
                image_file.stream.seek(0)
                with Image.open(image_file.stream) as im:
                    im.verify()
                image_file.stream.seek(0)
            except Exception:
                flash("Uploaded file is not a valid image.", "danger")
                return render_template("admin/post_form.html", categories=Category.query.order_by(Category.CategoryName).all(), subcategories=SubCategory.query.order_by(SubCategory.Subcategory).all(), post=post)
            unique_name = f"{name}_{uuid.uuid4().hex[:8]}{ext.lower()}"
            upload_dir = current_app.config.get("UPLOAD_FOLDER")
            os.makedirs(upload_dir, exist_ok=True)
            image_path = os.path.join(upload_dir, unique_name)
            try:
                image_file.save(image_path)
            except Exception:
                flash("Failed to save image.", "danger")
                return render_template("admin/post_form.html", categories=Category.query.order_by(Category.CategoryName).all(), subcategories=SubCategory.query.order_by(SubCategory.Subcategory).all(), post=post)
            if hasattr(post, 'PostImage'):
                post.PostImage = unique_name
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
    db.session.delete(post)
    db.session.commit()
    flash("Post deleted", "success")
    return redirect(url_for("admin.posts_list"))


# Editor asset uploads (Quill image upload)
@bp.post("/posts/upload-image")
@login_required
def posts_upload_image():
    image_file = request.files.get("image")
    if not image_file or not image_file.filename:
        return jsonify({"error": "No image provided"}), 400
    # basic content-type guard
    if not (image_file.mimetype or '').startswith('image/'):
        return jsonify({"error": "Unsupported file type"}), 415
    # Magic-byte validation using Pillow
    try:
        image_file.stream.seek(0)
        with Image.open(image_file.stream) as im:
            im.verify()
        image_file.stream.seek(0)
    except Exception:
        return jsonify({"error": "Invalid image"}), 415
    # Sanitize and uniquify filename
    base = secure_filename(image_file.filename)
    name, ext = os.path.splitext(base)
    unique_name = f"{name}_{uuid.uuid4().hex[:8]}{ext}" if ext else f"{name}_{uuid.uuid4().hex[:8]}"
    upload_dir = current_app.config.get("UPLOAD_FOLDER")
    try:
        os.makedirs(upload_dir, exist_ok=True)
        image_path = os.path.join(upload_dir, unique_name)
        image_file.save(image_path)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    # Serve from /static/uploads/<file> if UPLOAD_FOLDER points there
    try:
        url = url_for("static", filename=f"uploads/{unique_name}")
    except Exception:
        # Fallback: relative path
        url = f"/static/uploads/{unique_name}"
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
        cat = Category(CategoryName=name, Description=desc, Is_Active=is_active)
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
        sub = SubCategory(Subcategory=name, SubCatDescription=desc, CategoryId=category_id, Is_Active=is_active)
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
        pg = Page(PageName=name, PageTitle=title, Description=desc)
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
        user = Admin(AdminUserName=username, AdminEmailId=email, AdminPassword=hashed, userType=1)
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
