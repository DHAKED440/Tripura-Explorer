"""Application factory for Tripura Explore.

``create_app`` wires configuration, extensions, blueprints, error pages,
template helpers and command line tasks into a single Flask application.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path

from flask import Flask, g, render_template

from app.config import get_config
from app.extensions import csrf, db, login_manager, migrate

__all__ = ["create_app"]


def create_app(config_name: str | None = None) -> Flask:
    """Build and return a configured Flask application."""
    app = Flask(__name__)
    app.config.from_object(get_config(config_name))

    Path(app.config["INSTANCE_DIR"]).mkdir(parents=True, exist_ok=True)

    _configure_logging(app)
    _register_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    _register_template_context(app)
    _register_cli(app)

    app.logger.info("Tripura Explore started in %s mode", app.config.get("ENV", "development"))
    return app


def _configure_logging(app: Flask) -> None:
    level = getattr(logging, str(app.config.get("LOG_LEVEL", "INFO")).upper(), logging.INFO)
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")


def _register_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    if app.config.get("TESTING"):
        # Session protection relies on client IP/user agent, which the Flask test
        # client does not vary. Turning it off keeps the tests deterministic.
        login_manager.session_protection = None

        @app.before_request
        def _reset_test_login_state():
            # A test can run several clients inside one long-lived app context, so
            # purge the user Flask-Login cached on ``g`` during a previous request.
            # Production requests always get a fresh context and never need this.
            g.pop("_login_user", None)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id: str):
        """Restore the logged in user from the session."""
        if not user_id:
            return None
        return db.session.get(User, int(user_id))


def _register_blueprints(app: Flask) -> None:
    from app.routes.admin import bp as admin_bp
    from app.routes.auth import bp as auth_bp
    from app.routes.experiences import bp as experiences_bp
    from app.routes.itineraries import bp as itineraries_bp
    from app.routes.main import bp as main_bp
    from app.routes.map import bp as map_bp
    from app.routes.places import bp as places_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(places_bp)
    app.register_blueprint(map_bp)
    app.register_blueprint(itineraries_bp)
    app.register_blueprint(experiences_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)


def _register_error_handlers(app: Flask) -> None:
    @app.errorhandler(404)
    def not_found(error):  # pragma: no cover - rendered by the test client too
        return render_template("errors/404.html"), 404

    @app.errorhandler(403)
    def forbidden(error):  # pragma: no cover
        return render_template("errors/403.html"), 403

    @app.errorhandler(500)
    def server_error(error):  # pragma: no cover
        db.session.rollback()
        return render_template("errors/500.html"), 500


def _register_template_context(app: Flask) -> None:
    from app.services.destination_service import get_interest_options

    @app.context_processor
    def inject_globals():
        return {
            "current_year": __import__("datetime").date.today().year,
            "site_name": "Tripura Explore",
            "site_tagline": "Discover the hidden beauty of Tripura.",
            "interest_options": get_interest_options(),
            "map_settings": {
                "tile_url": app.config["MAP_TILE_URL"],
                "attribution": app.config["MAP_TILE_ATTRIBUTION"],
                "center": app.config["MAP_DEFAULT_CENTER"],
                "zoom": app.config["MAP_DEFAULT_ZOOM"],
                "max_zoom": app.config["MAP_MAX_ZOOM"],
            },
        }


def _register_cli(app: Flask) -> None:
    from app import cli

    cli.register(app)


def create_app_from_env() -> Flask:
    """Helper used by ``flask --app`` style entry points."""
    return create_app(os.environ.get("FLASK_CONFIG", "development"))