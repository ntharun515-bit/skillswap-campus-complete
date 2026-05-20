"""Security helpers: sanitization, file validation, activity logging."""
import os
import re
import bleach
from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from backend.extensions import db
from backend.models import User, ActivityLog


ALLOWED_TAGS = []
ALLOWED_ATTRIBUTES = {}


def sanitize_text(text):
    """Remove HTML/scripts from user input to prevent XSS."""
    if not text:
        return text
    return bleach.clean(str(text), tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES, strip=True)


def allowed_file(filename, allowed_extensions):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def secure_filename_custom(filename):
    """Keep only safe characters in uploaded filenames."""
    name = os.path.basename(filename)
    return re.sub(r"[^a-zA-Z0-9._-]", "", name)


def log_activity(user_id, action, details=None):
    from datetime import datetime
    log = ActivityLog(
        user_id=user_id,
        action=action,
        details=details,
        ip_address=request.remote_addr,
    )
    db.session.add(log)
    db.session.commit()

    try:
        from backend.extensions import socketio
        socketio.emit("admin_activity", {
            "action": action,
            "details": details or "",
            "created_at": datetime.utcnow().isoformat() + "Z"
        })
    except Exception:
        pass


def role_required(*roles):
    """Decorator: JWT required and user must have one of the given roles."""

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(int(user_id))
            if not user or user.is_banned or not user.is_active:
                return jsonify({"error": "Account suspended or inactive"}), 403
            if user.role.name not in roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            return fn(*args, **kwargs)

        return wrapper

    return decorator
