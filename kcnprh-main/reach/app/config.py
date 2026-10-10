import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    _database_url = os.getenv("DATABASE_URL", "sqlite:///reach.sqlite3")
    if _database_url.startswith("postgres://"):
        _database_url = _database_url.replace("postgres://", "postgresql+psycopg2://", 1)
    SQLALCHEMY_DATABASE_URI = _database_url
    if _database_url.startswith("sqlite:"):
        SQLALCHEMY_ENGINE_OPTIONS = {
            "execution_options": {
                "schema_translate_map": {"newsportal": None},
            },
        }
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Flask settings
    DEBUG = os.getenv("FLASK_ENV") == "development"
    # Uploads
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", os.path.join(os.path.dirname(__file__), "static", "uploads"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 20 * 1024 * 1024))  # 20 MB default
    # Cookies/security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = os.getenv("SESSION_COOKIE_SAMESITE", "Lax")
    SESSION_COOKIE_SECURE = os.getenv("FLASK_ENV") == "production"
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = os.getenv("REMEMBER_COOKIE_SAMESITE", "Lax")
    REMEMBER_COOKIE_SECURE = os.getenv("FLASK_ENV") == "production"
    # URL building
    PREFERRED_URL_SCHEME = os.getenv("PREFERRED_URL_SCHEME", "https")


class DevelopmentConfig(Config):
    """Settings for local development.

    - Disable static file caching
    - Enable template auto-reload
    - Force DEBUG on
    """
    DEBUG = True
    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0
