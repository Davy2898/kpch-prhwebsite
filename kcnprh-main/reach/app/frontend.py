import re
import bleach
from flask import Blueprint, redirect, render_template, request, url_for
from .models import Post

bp = Blueprint("frontend", __name__)


@bp.get("/")
@bp.get("/news")
@bp.get("/updates")
@bp.get("/about")
@bp.get("/contact")
@bp.get("/search")
@bp.get("/category/<int:_category_id>")
@bp.get("/post/<int:_post_id>")
@bp.get("/page/<string:_slug>")
@bp.get("/services/<string:_service_slug>")
def vue_app(_category_id=None, _post_id=None, _slug=None, _service_slug=None):
    proto = request.headers.get("X-Forwarded-Proto") or request.scheme or "http"
    host = request.headers.get("X-Forwarded-Host") or request.host
    cf_visitor = request.headers.get("Cf-Visitor", "")
    if "https" in cf_visitor or "trycloudflare.com" in host:
        proto = "https"
    base_url = f"{proto}://{host}"

    site_title = "មន្ទីរពេទ្យខេត្តកំពង់ឆ្នាំង | Kampong Chhnang Provincial Referral Hospital"
    site_desc = "ព័ត៌មាន និងសេចក្តីជូនដំណឹងពីមន្ទីរពេទ្យបង្អែកខេត្តកំពង់ឆ្នាំង ផ្តល់សេវាសុខាភិបាល ២៤ម៉ោងលើ២៤ម៉ោង ប្រកបដោយគុណភាព និងសុវត្ថិភាព។"
    site_image = f"{base_url}{url_for('static', filename='img/kampongchhnangentry.jpg')}"

    og = {
        "title": site_title,
        "description": site_desc,
        "image": site_image,
        "url": f"{base_url}{request.path}",
        "type": "website",
    }

    if _post_id:
        post = Post.query.filter_by(id=_post_id, Is_Active=1).first()
        if post:
            og["title"] = post.PostTitle or site_title
            og["type"] = "article"
            if post.PostDetails:
                cleaned_text = bleach.clean(post.PostDetails, tags=[], strip=True)
                trimmed_text = " ".join(cleaned_text.split())
                if trimmed_text:
                    og["description"] = trimmed_text[:250] + ("..." if len(trimmed_text) > 250 else "")
                else:
                    og["description"] = post.PostTitle or site_desc
            else:
                og["description"] = post.PostTitle or site_desc
            if post.PostImage:
                og["image"] = f"{base_url}{url_for('static', filename=f'uploads/{post.PostImage}')}"
            else:
                match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', post.PostDetails or "")
                if match:
                    img_src = match.group(1)
                    if img_src.startswith("http://") or img_src.startswith("https://"):
                        og["image"] = img_src
                    else:
                        og["image"] = base_url.rstrip("/") + "/" + img_src.lstrip("/")

    return render_template("vue.html", og=og)


@bp.get("/favicon.ico")
def favicon():
    return redirect(url_for("static", filename="img/logo.svg"))
