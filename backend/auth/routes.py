"""Authentication routes: register, login, logout, refresh, session."""
from flask import Blueprint, request, jsonify, session
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    set_access_cookies,
    set_refresh_cookies,
    unset_jwt_cookies,
)
from backend.extensions import db, limiter
from backend.models import User, Role, FreelancerProfile
from backend.utils import hash_password, verify_password, create_notification
from backend.middleware.security import sanitize_text, log_activity

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.route("/register", methods=["POST"])
@limiter.limit("10 per minute")
def register():
    data = request.get_json() or {}
    email = sanitize_text(data.get("email", "")).lower().strip()
    password = data.get("password", "")
    full_name = sanitize_text(data.get("full_name", ""))
    role_name = sanitize_text(data.get("role", "student"))
    campus = sanitize_text(data.get("campus", ""))

    if not email or not password or not full_name:
        return jsonify({"error": "Email, password, and full name are required"}), 400
    if len(password) < 8:
        return jsonify({"error": "Password must be at least 8 characters"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "Email already registered"}), 409

    role = Role.query.filter_by(name=role_name).first()
    if not role:
        if role_name == "client":
            role = Role.query.filter_by(name="client").first()
        else:
            role = Role.query.filter_by(name="student").first()
    if not role:
        return jsonify({"error": "Invalid role"}), 400

    user = User(
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        role_id=role.id,
        campus=campus,
    )
    db.session.add(user)
    db.session.flush()

    if role.name == "student":
        profile = FreelancerProfile(user_id=user.id, headline="Student Freelancer")
        db.session.add(profile)

    db.session.commit()
    log_activity(user.id, "register", f"Registered as {role.name}")
    create_notification(user.id, "Welcome!", "Welcome to SkillSwap. Complete your profile to get started.")

    access = create_access_token(identity=str(user.id))
    refresh = create_refresh_token(identity=str(user.id))
    resp = jsonify({
        "message": "Registration successful",
        "user": user.to_dict(include_email=True),
        "access_token": access,
        "refresh_token": refresh,
    })
    set_access_cookies(resp, access)
    set_refresh_cookies(resp, refresh)
    session["user_id"] = user.id
    return resp, 201


@auth_bp.route("/login", methods=["POST"])
@limiter.limit("15 per minute")
def login():
    data = request.get_json() or {}
    email = sanitize_text(data.get("email", "")).lower().strip()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()
    if not user or not verify_password(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401
    if user.is_banned:
        return jsonify({"error": "Account has been suspended"}), 403
    if not user.is_active:
        return jsonify({"error": "Account is inactive"}), 403

    user.is_online = True
    db.session.commit()
    log_activity(user.id, "login")

    access = create_access_token(identity=str(user.id))
    refresh = create_refresh_token(identity=str(user.id))
    resp = jsonify({
        "message": "Login successful",
        "user": user.to_dict(include_email=True),
        "access_token": access,
        "refresh_token": refresh,
    })
    set_access_cookies(resp, access)
    set_refresh_cookies(resp, refresh)
    session["user_id"] = user.id
    return resp


@auth_bp.route("/logout", methods=["POST"])
@jwt_required(optional=True)
def logout():
    user_id = get_jwt_identity()
    if user_id:
        user = User.query.get(int(user_id))
        if user:
            user.is_online = False
            db.session.commit()
            log_activity(user.id, "logout")
    session.pop("user_id", None)
    resp = jsonify({"message": "Logged out"})
    unset_jwt_cookies(resp)
    return resp


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    user_id = get_jwt_identity()
    access = create_access_token(identity=user_id)
    resp = jsonify({"access_token": access})
    set_access_cookies(resp, access)
    return resp


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def me():
    user = User.query.get(int(get_jwt_identity()))
    if not user:
        return jsonify({"error": "User not found"}), 404
    data = user.to_dict(include_email=True)
    if user.freelancer_profile:
        data["profile"] = user.freelancer_profile.to_dict()
    return jsonify(data)
