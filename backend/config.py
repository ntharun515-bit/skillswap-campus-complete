"""Application configuration loaded from environment variables."""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() == "true"
    JWT_COOKIE_CSRF_PROTECT = False

    use_sqlite = os.getenv("USE_SQLITE", "false").lower() == "true"
    _db_url = os.getenv("DATABASE_URL", "")
    if use_sqlite or not _db_url:
        _root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        _db_url = "sqlite:///" + os.path.join(_root, "database", "skillswap.db").replace("\\", "/")
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = (
        {"pool_pre_ping": True, "pool_recycle": 300}
        if _db_url.startswith("mysql")
        else {"connect_args": {"check_same_thread": False}}
    )

    UPLOAD_FOLDER = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", os.getenv("UPLOAD_FOLDER", "uploads"))
    )
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    ALLOWED_DOC_EXTENSIONS = {"pdf", "doc", "docx"}

    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5000").split(",")
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "200 per hour")
    HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN", "")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_ENABLED = True

    LOG_FILE = os.path.join(os.path.dirname(__file__), "..", "logs", "app.log")


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    JWT_COOKIE_SECURE = True


class TestingConfig(Config):
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL", "sqlite:///:memory:")
    WTF_CSRF_ENABLED = False


config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig,
}

