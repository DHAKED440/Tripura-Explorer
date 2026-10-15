"""Configuration objects for the Tripura Explore application.

Settings are read from environment variables (loaded from a local ``.env``
file when present).  Nothing secret is ever hard coded here: the placeholders
below are only usable for local development and are replaced by real values in
production.
"""
from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
INSTANCE_DIR = BASE_DIR / "instance"

# Load .env from the project root (a no-op when the file does not exist).
load_dotenv(BASE_DIR / ".env")


def default_database_uri() -> str:
    """Return the default SQLite database URI inside ``instance/``."""
    INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
    return "sqlite:///" + (INSTANCE_DIR / "tripura_explore.db").as_posix()


def env_bool(name: str, default: bool = False) -> bool:
    """Read a yes/no style environment variable."""
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    """Read an integer environment variable, falling back to ``default``."""
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


class Config:
    """Settings shared by every environment."""

    BASE_DIR = BASE_DIR
    INSTANCE_DIR = INSTANCE_DIR

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-secret-key-change-me")

    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or default_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # Session / cookie hardening (secure cookies are switched on in production).
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = env_bool("COOKIE_SECURE", False)
    REMEMBER_COOKIE_HTTPONLY = True
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=env_int("SESSION_LIFETIME_MINUTES", 120))
    WTF_CSRF_TIME_LIMIT = None

    # Interactive map settings. The tile URL is configurable so a self hosted or
    # licensed tile service can be used in production.
    MAP_TILE_URL = os.environ.get("MAP_TILE_URL", "https://tile.openstreetmap.org/{z}/{x}/{y}.png")
    MAP_TILE_ATTRIBUTION = os.environ.get(
        "MAP_TILE_ATTRIBUTION",
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    )
    MAP_MAX_ZOOM = env_int("MAP_MAX_ZOOM", 18)
    MAP_DEFAULT_CENTER = [23.8315, 91.2868]  # Agartala, Tripura
    MAP_DEFAULT_ZOOM = env_int("MAP_DEFAULT_ZOOM", 8)

    # Product rules
    PLACES_PER_PAGE = env_int("PLACES_PER_PAGE", 9)
    MIN_ITINERARY_DAYS = 1
    MAX_ITINERARY_DAYS = 3
    MAX_RESULTS_PER_DAY = 3

    # Bootstrap admin account used only by the ``seed-data`` command.
    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "")

    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    # Restricted server-side Google Places API (New) key. Never expose to browsers.
    GOOGLE_MAPS_API_KEY = (
        os.environ.get("GOOGLE_MAPS_API_KEY", "")
        .strip()
        .strip('"')
        .strip("'")
    )


class DevelopmentConfig(Config):
    """Local development."""

    DEBUG = True
    ENV = "development"


class TestingConfig(Config):
    """Automated tests: in-memory database, CSRF disabled."""

    TESTING = True
    ENV = "testing"
    SECRET_KEY = "testing-secret-key"
    SQLALCHEMY_DATABASE_URI = "sqlite://"
    WTF_CSRF_ENABLED = False
    SERVER_NAME = None
    ADMIN_EMAIL = "admin@example.com"
    ADMIN_PASSWORD = "admin-test-password"


class ProductionConfig(Config):
    """Production defaults. Secrets and the database URL must come from the environment."""

    DEBUG = False
    ENV = "production"
    SESSION_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = "https"


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config(name: str | None = None):
    """Return a configuration class by name."""
    if not name:
        name = os.environ.get("FLASK_CONFIG", "development")
    return CONFIG_MAP.get(name, DevelopmentConfig)
