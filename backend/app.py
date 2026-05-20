"""Flask application factory for SkillSwap."""
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, send_from_directory, jsonify
from backend.config import config_map
from backend.extensions import db, migrate, jwt, socketio, limiter, cors
from backend.auth import auth_bp
from backend.users import users_bp
from backend.projects import projects_bp
from backend.projects.teams_routes import teams_bp
from backend.chat import chat_bp
from backend.admin import admin_bp
from backend.ai import ai_bp
from backend.api import api_bp
from backend.payments import payments_bp
import backend.chat.socket_events  # noqa: F401 - register socket handlers


def create_app(config_name=None):
    app = Flask(
        __name__,
        static_folder=os.path.join(os.path.dirname(__file__), "..", "frontend"),
        static_url_path="/frontend",
    )
    env = config_name or os.getenv("FLASK_ENV", "development")
    app.config.from_object(config_map.get(env, config_map["default"]))

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "logs"), exist_ok=True)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    limiter.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}}, supports_credentials=True)
    socketio.init_app(app)

    with app.app_context():
        db.create_all()

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(teams_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(payments_bp)

    @jwt.expired_token_loader
    def expired_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Token expired"}), 401

    @jwt.invalid_token_loader
    def invalid_callback(error):
        return jsonify({"error": "Invalid token"}), 401

    @app.route("/")
    def index():
        return send_from_directory(app.static_folder, "pages/public/index.html")

    @app.route("/<string:page>.html")
    def serve_public_page(page):
        public_pages = {"index", "about", "contact", "faq", "freelancers", "login", "profile", "projects", "register"}
        if page in public_pages:
            return send_from_directory(app.static_folder, f"pages/public/{page}.html")
        return send_from_directory(app.static_folder, "pages/public/index.html")

    @app.route("/profile/<string:slug>")
    def public_profile_page(slug):
        return send_from_directory(app.static_folder, "pages/public/profile.html")

    @app.route("/freelancer/<string:slug>")
    def public_freelancer_page(slug):
        return send_from_directory(app.static_folder, "pages/public/profile.html")

    @app.route("/uploads/<path:filename>")
    def uploaded_file(filename):
        return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

    @app.route("/frontend/<path:path>")
    def serve_frontend(path):
        full = os.path.join(app.static_folder, path)
        if os.path.isfile(full):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, "pages/public/index.html")

    _setup_logging(app)
    _register_error_handlers(app)
    return app


def _register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request_error(error):
        app.logger.error(f"HTTP 400 Bad Request: {error}")
        return jsonify({"error": "Bad request", "message": str(error)}), 400

    @app.errorhandler(401)
    def unauthorized_error(error):
        app.logger.warning(f"HTTP 401 Unauthorized: {error}")
        return jsonify({"error": "Unauthorized Access", "message": str(error)}), 401

    @app.errorhandler(403)
    def forbidden_error(error):
        app.logger.warning(f"HTTP 403 Forbidden: {error}")
        return jsonify({"error": "Access Denied", "message": str(error)}), 403

    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.info(f"HTTP 404 Not Found: {error}")
        return jsonify({"error": "Resource Not Found", "message": str(error)}), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        app.logger.error(f"HTTP 500 Internal Server Error: {error}", exc_info=True)
        return jsonify({"error": "Internal Server Error", "message": "An unexpected server error occurred."}), 500


def _setup_logging(app):
    log_dir = os.path.join(os.path.dirname(__file__), "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "error.log")
    
    # Configure rotating file handler for production-grade logging
    handler = RotatingFileHandler(log_file, maxBytes=2048000, backupCount=10)
    handler.setFormatter(logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s (%(process)d): %(message)s"
    ))
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)


app = create_app()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)
