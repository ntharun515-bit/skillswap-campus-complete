"""Flask-SocketIO real-time chat, typing, notifications, presence."""
from datetime import datetime
from flask import request, session
from flask_jwt_extended import decode_token
from flask_socketio import emit, join_room, leave_room
from backend.extensions import db, socketio
from backend.models import User, Message, Conversation, Notification
from backend.middleware.security import sanitize_text
from backend.utils import create_notification


@socketio.on("connect")
def on_connect():
    db.session.remove()
    token = request.args.get("token") or request.headers.get("Authorization", "").replace("Bearer ", "")
    if not token:
        return False
    try:
        decoded = decode_token(token)
        user_id = int(decoded["sub"])
        user = User.query.get(user_id)
        if not user or user.is_banned:
            return False
        request.user_id = user_id
        session["user_id"] = user_id
        user.is_online = True
        user.last_seen = datetime.utcnow()
        db.session.commit()
        join_room(f"user_{user_id}")
        emit("connected", {"user_id": user_id})
        emit("user_online", {"user_id": user_id}, broadcast=True)
    except Exception:
        return False


@socketio.on("disconnect")
def on_disconnect():
    user_id = session.get("user_id") or getattr(request, "user_id", None)
    if user_id:
        user = User.query.get(user_id)
        if user:
            user.is_online = False
            user.last_seen = datetime.utcnow()
            db.session.commit()
        leave_room(f"user_{user_id}")
        emit("user_offline", {"user_id": user_id}, broadcast=True)


@socketio.on("join_conversation")
def join_conversation(data):
    conv_id = data.get("conversation_id")
    join_room(f"conv_{conv_id}")


@socketio.on("leave_conversation")
def leave_conversation(data):
    conv_id = data.get("conversation_id")
    leave_room(f"conv_{conv_id}")


@socketio.on("send_message")
def handle_message(data):
    db.session.remove()
    user_id = session.get("user_id") or getattr(request, "user_id", None)
    if not user_id:
        return
    conv_id = data.get("conversation_id")
    content = sanitize_text(data.get("content", ""))
    if not content:
        return
    conv = Conversation.query.get(conv_id)
    if not conv or user_id not in (conv.participant_one, conv.participant_two):
        return
    msg = Message(conversation_id=conv_id, sender_id=user_id, content=content)
    db.session.add(msg)
    db.session.commit()
    payload = msg.to_dict()
    emit("new_message", payload, room=f"conv_{conv_id}")
    other_id = conv.participant_two if conv.participant_one == user_id else conv.participant_one
    other_user = User.query.get(other_id)
    dest_path = "student" if (other_user and other_user.role.name == "student") else "client"
    create_notification(other_id, "New Message", content[:80], "message", f"/frontend/pages/{dest_path}/messages.html?conv={conv_id}")
    emit("notification", {"title": "New Message", "message": content[:80]}, room=f"user_{other_id}")


@socketio.on("typing")
def handle_typing(data):
    user_id = session.get("user_id") or getattr(request, "user_id", None)
    conv_id = data.get("conversation_id")
    emit("typing", {"user_id": user_id, "conversation_id": conv_id}, room=f"conv_{conv_id}", include_self=False)


@socketio.on("stop_typing")
def handle_stop_typing(data):
    user_id = session.get("user_id") or getattr(request, "user_id", None)
    conv_id = data.get("conversation_id")
    emit("stop_typing", {"user_id": user_id, "conversation_id": conv_id}, room=f"conv_{conv_id}", include_self=False)


# =========================================================================
# MULTI-USER COLLABORATIVE TEAM SOCKET EVENTS
# =========================================================================

from backend.models import Team, TeamMember, TeamMessage, KanbanTask

@socketio.on("join_team")
def handle_join_team(data):
    user_id = session.get("user_id") or getattr(request, "user_id", None)
    if not user_id:
        return
    team_id = data.get("team_id")
    # Verify membership
    mem = TeamMember.query.filter_by(team_id=team_id, user_id=user_id).first()
    if mem:
        join_room(f"team_{team_id}")
        emit("team_joined", {"team_id": team_id})


@socketio.on("leave_team")
def handle_leave_team(data):
    team_id = data.get("team_id")
    leave_room(f"team_{team_id}")


@socketio.on("send_team_message")
def handle_send_team_message(data):
    user_id = session.get("user_id") or getattr(request, "user_id", None)
    if not user_id:
        return
    team_id = data.get("team_id")
    content = sanitize_text(data.get("message", ""))
    if not content:
        return
        
    mem = TeamMember.query.filter_by(team_id=team_id, user_id=user_id).first()
    if not mem:
        return
        
    msg = TeamMessage(team_id=team_id, sender_id=user_id, message=content)
    db.session.add(msg)
    db.session.commit()
    
    payload = msg.to_dict()
    emit("new_team_message", payload, room=f"team_{team_id}")
    
    # Send notifications to all other team members in real-time
    team = Team.query.get(team_id)
    sender = User.query.get(user_id)
    for m in team.members:
        if m.user_id != user_id:
            # Emit live browser notification
            create_notification(
                user_id=m.user_id,
                title=f"💬 {team.name} Chat",
                message=f"{sender.full_name}: {content[:60]}",
                ntype="message",
                link="/frontend/pages/student/workspace.html"
            )
            emit("notification", {"title": f"💬 {team.name}", "message": f"{sender.full_name}: {content[:60]}"}, room=f"user_{m.user_id}")


@socketio.on("team_typing")
def handle_team_typing(data):
    user_id = session.get("user_id") or getattr(request, "user_id", None)
    team_id = data.get("team_id")
    user = User.query.get(user_id)
    if user:
        emit("team_typing", {"user_id": user_id, "user_name": user.full_name, "team_id": team_id}, room=f"team_{team_id}", include_self=False)


@socketio.on("team_stop_typing")
def handle_team_stop_typing(data):
    user_id = session.get("user_id") or getattr(request, "user_id", None)
    team_id = data.get("team_id")
    emit("team_stop_typing", {"user_id": user_id, "team_id": team_id}, room=f"team_{team_id}", include_self=False)


@socketio.on("move_team_task")
def handle_move_team_task(data):
    db.session.remove()
    user_id = session.get("user_id") or getattr(request, "user_id", None)
    if not user_id:
        return
    team_id = data.get("team_id")
    task_id = data.get("task_id")
    target_column = data.get("column") # todo, in_progress, review, done
    
    # Check membership
    mem = TeamMember.query.filter_by(team_id=team_id, user_id=user_id).first()
    if not mem:
        return
        
    task = KanbanTask.query.get(task_id)
    if not task:
        return
        
    task.column = target_column
    db.session.commit()
    
    # Broadcast task movement to all team members instantly
    emit("team_task_moved", {
        "task_id": task_id,
        "column": target_column,
        "moved_by_name": mem.user.full_name
    }, room=f"team_{team_id}", include_self=False)

