import os

from app import create_app, db


def make_app():
    os.makedirs("instance", exist_ok=True)
    db_file = os.path.join("instance", "reach.sqlite3")
    seed_file = "reach_seed.sqlite3"
    if (not os.path.exists(db_file) or os.path.getsize(db_file) == 0) and os.path.exists(seed_file):
        import shutil
        shutil.copyfile(seed_file, db_file)

    return create_app(
        {
            "SQLALCHEMY_DATABASE_URI": "sqlite:///reach.sqlite3",
            "SQLALCHEMY_ENGINE_OPTIONS": {
                "execution_options": {
                    "schema_translate_map": {"newsportal": None},
                },
            },
        }
    )


app = make_app()

with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True, use_reloader=False)
