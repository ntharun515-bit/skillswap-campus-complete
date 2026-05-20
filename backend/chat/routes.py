"""REST API for conversations and messages."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_
from backend.extensions import db
from backend.models import Conversation, Message, User

chat_bp = Blueprint("chat", __name__, url_prefix="/api/chat")


def get_or_create_conversation(user1, user2, project_id=None):
    conv = Conversation.query.filter(
        or_(
            (Conversation.participant_one == user1) & (Conversation.participant_two == user2),
            (Conversation.participant_one == user2) & (Conversation.participant_two == user1),
        )
    ).first()
    if not conv:
        conv = Conversation(participant_one=user1, participant_two=user2, project_id=project_id)
        db.session.add(conv)
        db.session.commit()
    return conv


@chat_bp.route("/conversations", methods=["GET"])
@jwt_required()
def list_conversations():
    user_id = int(get_jwt_identity())
    convs = Conversation.query.filter(
        or_(Conversation.participant_one == user_id, Conversation.participant_two == user_id)
    ).order_by(Conversation.created_at.desc()).all()
    result = []
    for c in convs:
        other_id = c.participant_two if c.participant_one == user_id else c.participant_one
        other = User.query.get(other_id)
        last_msg = Message.query.filter_by(conversation_id=c.id).order_by(Message.created_at.desc()).first()
        result.append({
            "id": c.id,
            "other_user": other.to_dict() if other else None,
            "last_message": last_msg.to_dict() if last_msg else None,
            "project_id": c.project_id,
        })
    return jsonify(result)


@chat_bp.route("/conversations", methods=["POST"])
@jwt_required()
def start_conversation():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    other_id = data.get("user_id")
    if not other_id:
        return jsonify({"error": "user_id required"}), 400
    conv = get_or_create_conversation(user_id, other_id, data.get("project_id"))
    return jsonify({"conversation_id": conv.id})


@chat_bp.route("/conversations/<int:conv_id>/messages", methods=["GET"])
@jwt_required()
def get_messages(conv_id):
    user_id = int(get_jwt_identity())
    conv = Conversation.query.get_or_404(conv_id)
    if user_id not in (conv.participant_one, conv.participant_two):
        return jsonify({"error": "Forbidden"}), 403
    messages = Message.query.filter_by(conversation_id=conv_id).order_by(Message.created_at.asc()).all()
    Message.query.filter_by(conversation_id=conv_id).filter(Message.sender_id != user_id).update({"is_read": True})
    db.session.commit()
    return jsonify([m.to_dict() for m in messages])
