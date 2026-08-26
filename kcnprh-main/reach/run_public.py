import os

from flask import abort, request

from app import create_app, db


def make_app():
    os.makedirs("instance", exist_ok=True)
    return create_app(
        {
            "DEBUG": False,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///reach.sqlite3",
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "execution_options": {
                    "schema_translate_map": {"newsportal": None},
                },
            },
        }
    )


app = make_app()


@app.before_request
def block_admin_on_public_preview():
    if request.path.startswith("/admin"):
        abort(404)


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=False, use_reloader=False)
