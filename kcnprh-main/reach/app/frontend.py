from flask import Blueprint, render_template

bp = Blueprint("frontend", __name__)


@bp.get("/")
@bp.get("/about")
@bp.get("/contact")
@bp.get("/search")
@bp.get("/category/<int:_category_id>")
@bp.get("/post/<int:_post_id>")
@bp.get("/page/<string:_slug>")
@bp.get("/services/<string:_service_slug>")
def vue_app(_category_id=None, _post_id=None, _slug=None, _service_slug=None):
    return render_template("vue.html")
