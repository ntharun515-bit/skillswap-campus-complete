"""Shared utility functions."""
import os
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app
from backend.middleware.security import secure_filename_custom, allowed_file


def hash_password(password):
    return generate_password_hash(password)


def verify_password(password_hash, password):
    return check_password_hash(password_hash, password)


def save_upload(file, subfolder, allowed_extensions):
    """Save uploaded file securely and return relative path."""
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename, allowed_extensions):
        raise ValueError("Invalid file type")
    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    folder = os.path.join(current_app.config["UPLOAD_FOLDER"], subfolder)
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, filename)
    file.save(path)
    return f"{subfolder}/{filename}"


def create_notification(user_id, title, message, ntype="info", link=None, priority="normal"):
    from backend.models import Notification
    from backend.extensions import db

    n = Notification(user_id=user_id, title=title, message=message, type=ntype, link=link, priority=priority)
    db.session.add(n)
    db.session.commit()
    return n
