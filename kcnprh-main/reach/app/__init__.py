import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
from flask_wtf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf.csrf import generate_csrf, CSRFError

# Globals
db = SQLAlchemy()
migrate = Migrate()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)


def create_app(test_config: dict | None = None) -> Flask:
    """Application factory for the reach Flask app."""
    # Load environment variables from .env if present
    load_dotenv()

    app = Flask(__name__, instance_relative_config=False)

    # Base config
    from .config import Config, DevelopmentConfig
    app.config.from_object(Config())

    # If running in development, layer DevelopmentConfig on top
    if os.getenv("FLASK_ENV") == "development" or os.getenv("FLASK_DEBUG") in {"1", "true", "True"}:
        app.config.from_object(DevelopmentConfig())

    # Allow test overrides
    if test_config:
        app.config.update(test_config)

    # Enforce proper secret key in production
    if os.getenv("FLASK_ENV") == "production" and app.config.get("SECRET_KEY") in {None, "", "change-me"}:
        raise RuntimeError("SECRET_KEY must be set to a strong value in production")

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    # Rate limiting (Flask-Limiter 3.x): configure storage via app.config
    app.config.setdefault("RATELIMIT_STORAGE_URI", os.getenv("RATELIMIT_STORAGE", "memory://"))
    limiter.init_app(app)
    # Import models so Alembic can detect them
    with app.app_context():
        from . import models  # noqa: F401

    # Make csrf_token available in templates for non-FlaskForm forms
    @app.context_processor
    def inject_csrf_token():
        # Expose a simple production flag to templates (used to switch Tailwind CDN vs built CSS)
        return dict(csrf_token=generate_csrf, is_prod=(os.getenv("FLASK_ENV") == "production"))

    # CSRF error handler
    @app.errorhandler(CSRFError)
    def handle_csrf_error(e: CSRFError):
        from flask import redirect, request, flash, url_for
        flash("Security check failed (CSRF). Please try again.", "danger")
        # Try to go back to referrer or home
        return redirect(request.referrer or url_for("frontend.vue_app")), 302

    # Security headers (CSP differs in dev vs production)
    @app.after_request
    def add_security_headers(resp):
        resp.headers.setdefault("X-Content-Type-Options", "nosniff")
        resp.headers.setdefault("X-Frame-Options", "DENY")
        resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        is_prod = os.getenv("FLASK_ENV") == "production"
        if is_prod:
            # Strict CSP in production; prefer self-hosted assets
            csp = (
                "default-src 'self'; "
                # Images (site assets + ad beacons/creatives)
                "img-src 'self' data: blob: https://googleads.g.doubleclick.net https://tpc.googlesyndication.com https://pagead2.googlesyndication.com https://ep1.adtrafficquality.google https://ep2.adtrafficquality.google; "
                # Styles (self + Google Fonts + CDNs used)
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
                # Scripts (inline + JSDelivr if needed + AdSense + Cloudflare Insights + AdTrafficQuality ep2)
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://pagead2.googlesyndication.com https://static.cloudflareinsights.com https://ep2.adtrafficquality.google; "
                # XHR/fetch (self + Google ad/analytics endpoints)
                "connect-src 'self' https://pagead2.googlesyndication.com https://googleads.g.doubleclick.net https://tpc.googlesyndication.com https://ep1.adtrafficquality.google https://ep2.adtrafficquality.google; "
                # Fonts (self + Google Fonts + cdnjs)
                "font-src 'self' data: https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
                # Frames (embedded Google properties + AdSense frames + AdTrafficQuality ep2)
                "frame-src 'self' https://www.facebook.com https://web.facebook.com https://www.google.com https://maps.google.com https://googleads.g.doubleclick.net https://tpc.googlesyndication.com https://pagead2.googlesyndication.com https://ep2.adtrafficquality.google;"
            )
        else:
            # Development: allow common CDNs used by the templates
            # Note: Production CSP remains strict; prefer self-hosted assets there.
            csp = (
                "default-src 'self'; "
                "img-src 'self' data: blob:; "
                "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdnjs.cloudflare.com https://cdn.jsdelivr.net; "
                "font-src 'self' data: https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.tailwindcss.com https://cdn.jsdelivr.net; "
                "connect-src 'self' ws:; "
                "frame-src 'self' https://www.facebook.com https://web.facebook.com https://www.google.com https://maps.google.com;"
            )
        resp.headers.setdefault("Content-Security-Policy", csp)
        return resp

    # Register blueprints
    from .api import bp as api_bp
    from .frontend import bp as frontend_bp
    from .admin import bp as admin_bp
    app.register_blueprint(api_bp)
    app.register_blueprint(frontend_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # Simple health endpoint
    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app
