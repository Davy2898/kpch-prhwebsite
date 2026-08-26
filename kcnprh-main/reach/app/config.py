import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///instance/reach.sqlite3",
    )
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
