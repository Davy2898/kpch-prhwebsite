from flask import Blueprint, render_template, abort, request, redirect, url_for, flash
import os
import json
from urllib import request as urlrequest
from urllib.parse import urlencode
from sqlalchemy import desc, or_
from ..models import Post, Category, SubCategory, Comment, Page
from .. import db

bp = Blueprint("public", __name__, template_folder="../templates")


@bp.get("/")
def home():
    page = request.args.get("page", 1, type=int)
    per_page = 10
    section = request.args.get("section", type=str)

    # Load categories first to support name-based matching
    categories = Category.query.order_by(Category.CategoryName).all()
    # Top viewed posts for trending sidebar (independent of pagination/category filter)
    try:
        trending_posts = (
            Post.query.filter_by(Is_Active=1)
            .order_by(desc(Post.viewCounter))
            .limit(8)
            .all()
        )
    except Exception:
        trending_posts = []

    def norm(name: str) -> str:
        s = (name or "").strip().lower()
        s = s.replace("&", "and").replace("/", " ")
        s = "-".join(filter(None, s.split()))
        return s

    cat_filter = None
    if section:
        sec = norm(section)
        for c in categories:
            if sec in {norm(c.CategoryName), (c.CategoryName or "").strip().lower()}:
                cat_filter = c
                break

    base_query = Post.query.filter_by(Is_Active=1)
    if cat_filter:
        base_query = base_query.filter_by(CategoryId=cat_filter.id)

    q = base_query.order_by(desc(Post.PostingDate))
    total = q.count()
    posts = q.offset((page - 1) * per_page).limit(per_page).all()

    # Preserve section in pagination links when present
    prev_url = None
    next_url = None
    if page > 1:
        prev_url = url_for("public.home", page=page - 1, section=section) if section else url_for("public.home", page=page - 1)
    if (page * per_page) < total:
        next_url = url_for("public.home", page=page + 1, section=section) if section else url_for("public.home", page=page + 1)

    pagination = {
        "page": page,
        "per_page": per_page,
        "total": total,
        "has_prev": page > 1,
        "has_next": (page * per_page) < total,
        "prev_url": prev_url,
        "next_url": next_url,
    }
    return render_template(
        "index.html",
        posts=posts,
        categories=categories,
        pagination=pagination,
        section=section,
        current_category=cat_filter,
        trending_posts=trending_posts,
    )


@bp.get("/category/<int:category_id>")
def category_view(category_id: int):
    category = Category.query.get_or_404(category_id)
    page = request.args.get("page", 1, type=int)
    per_page = 10
    q = Post.query.filter_by(CategoryId=category_id, Is_Active=1).order_by(desc(Post.PostingDate))
    total = q.count()
    posts = q.offset((page - 1) * per_page).limit(per_page).all()
    pagination = {
        "page": page,
        "per_page": per_page,
        "total": total,
        "has_prev": page > 1,
        "has_next": (page * per_page) < total,
        "prev_url": url_for("public.category_view", category_id=category_id, page=page - 1) if page > 1 else None,
        "next_url": url_for("public.category_view", category_id=category_id, page=page + 1) if (page * per_page) < total else None,
    }
    return render_template("category.html", category=category, posts=posts, pagination=pagination)


@bp.get("/post/<int:post_id>")
def post_detail(post_id: int):
    post = Post.query.get_or_404(post_id)
    if not post.Is_Active:
        abort(404)
    # increment view counter
    try:
        post.viewCounter = (post.viewCounter or 0) + 1
        db.session.commit()
    except Exception:
        db.session.rollback()
    comments = Comment.query.filter_by(postId=post_id, status=1).order_by(desc(Comment.postingDate)).all()
    return render_template("post_detail.html", post=post, comments=comments)


@bp.post("/post/<int:post_id>/comment")
def submit_comment(post_id: int):
    post = Post.query.get_or_404(post_id)
    if not post.Is_Active:
        abort(404)
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    text = request.form.get("comment", "").strip()
    if not name or not email or not text:
        flash("Please provide name, email, and comment.", "warning")
        return redirect(url_for("public.post_detail", post_id=post_id))
    cm = Comment(postId=post_id, name=name, email=email, comment=text, status=0)
    db.session.add(cm)
    db.session.commit()
    flash("Comment submitted and awaiting approval.", "success")
    return redirect(url_for("public.post_detail", post_id=post_id))


@bp.get("/search")
def search():
    qstr = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = 10
    posts = []
    total = 0
    if qstr:
        q = Post.query.filter(
            Post.Is_Active == 1,
            or_(Post.PostTitle.ilike(f"%{qstr}%"), Post.PostDetails.ilike(f"%{qstr}%")),
        ).order_by(desc(Post.PostingDate))
        total = q.count()
        posts = q.offset((page - 1) * per_page).limit(per_page).all()
    pagination = {
        "page": page,
        "per_page": per_page,
        "total": total,
        "has_prev": page > 1,
        "has_next": (page * per_page) < total,
        "prev_url": url_for("public.search", q=qstr, page=page - 1) if page > 1 else None,
        "next_url": url_for("public.search", q=qstr, page=page + 1) if (page * per_page) < total else None,
    }
    categories = Category.query.order_by(Category.CategoryName).all()
    return render_template("index.html", posts=posts, categories=categories, pagination=pagination, q=qstr)


@bp.get("/about")
def about():
    return render_template("about.html")


@bp.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        phone = (request.form.get("phone") or "").strip()
        email = (request.form.get("email") or "").strip()
        reason = (request.form.get("case") or "").strip()
        department = (request.form.get("pidaddep") or "").strip()
        dt = (request.form.get("datetime") or "").strip()
        if not name or not phone or not reason or not dt:
            flash("សូមបំពេញព័ត៌មានចាំបាច់ (Name, Phone, Root case, Date)", "warning")
        else:
            # Attempt to send a Telegram message using Bot API
            token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
            chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
            if token and chat_id:
                try:
                    msg_lines = [
                        "📩 New Appointment Request",
                        f"• Name: {name}",
                        f"• Phone: {phone}",
                        (f"• Email: {email}" if email else None),
                        f"• Department: {department or '-'}",
                        f"• Reason: {reason}",
                        f"• DateTime: {dt}"
                    ]
                    text = "\n".join([line for line in msg_lines if line])
                    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
                    payload = {
                        "chat_id": chat_id,
                        "text": text,
                        "parse_mode": "HTML",
                        "disable_web_page_preview": True,
                    }
                    data = urlencode(payload).encode()
                    req = urlrequest.Request(api_url, data=data, headers={"Content-Type": "application/x-www-form-urlencoded"})
                    with urlrequest.urlopen(req, timeout=8) as resp:
                        body = resp.read()
                        try:
                            data_json = json.loads(body.decode('utf-8'))
                        except Exception:
                            data_json = None
                        if not data_json or data_json.get('ok') is not True:
                            # Telegram returned error (e.g., bot not in chat). Surface description if available.
                            desc = (data_json or {}).get('description') if isinstance(data_json, dict) else None
                            flash(f"បរាជ័យក្នុងការផ្ញើទៅ Telegram: {desc or 'Unknown error'}", "warning")
                except Exception:
                    # Non-fatal: just inform user it couldn't notify Telegram
                    flash("បានទទួលព័ត៍មាន — ប៉ុន្តែការផ្ញើទៅ Telegram បរាជ័យ.", "warning")
            else:
                # Env not configured
                flash("ត្រូវការកំណត់ TELEGRAM_BOT_TOKEN និង TELEGRAM_CHAT_ID ដើម្បីផ្ញើ Telegram.", "warning")
            flash("បានទទួលព័ត៍មានការណាត់ជួបរបស់អ្នករួចរាល់!", "success")
    return render_template("contact.html")


@bp.get("/page/<string:slug>")
def static_page(slug: str):
    page_obj = Page.query.filter(Page.PageName == slug).first_or_404()
    return render_template("page.html", page=page_obj)

# Back-compat: allow url_for('public.page', slug=...) to resolve via an explicit alias view
@bp.get("/page/<string:slug>", endpoint="page")
def static_page_alias(slug: str):
    return static_page(slug)


# Serve a favicon for browsers that request /favicon.ico
@bp.get("/favicon.ico")
def favicon():
    # Redirect to the SVG logo used as favicon
    return redirect(url_for("static", filename="img/logo.svg"))
