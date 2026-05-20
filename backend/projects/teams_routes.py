"""Blueprint for multi-user student team collaboration, workspaces, and chat APIs."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models import User, Team, TeamMember, TeamInvitation, TeamMessage, Project, KanbanTask
from backend.extensions import db, socketio
from backend.middleware.security import sanitize_text
from backend.utils import create_notification

teams_bp = Blueprint("teams", __name__, url_prefix="/api/teams")


@teams_bp.route("", methods=["GET", "POST"])
@jwt_required()
def manage_teams():
    """Create a new team or retrieve list of teams the user is member of."""
    user_id = int(get_jwt_identity())
    
    if request.method == "POST":
        data = request.get_json() or {}
        name = sanitize_text(data.get("name", "")).strip()
        description = sanitize_text(data.get("description", "")).strip()
        
        if not name:
            return jsonify({"error": "Team name is required"}), 400
            
        team = Team(name=name, description=description, created_by=user_id)
        db.session.add(team)
        db.session.flush()
        
        # Creator is automatically added as Team Leader
        leader = TeamMember(team_id=team.id, user_id=user_id, role="Team Leader")
        db.session.add(leader)
        db.session.commit()
        
        return jsonify(team.to_dict()), 201
        
    # GET: Retrieve teams where user is a member
    member_records = TeamMember.query.filter_by(user_id=user_id).all()
    teams_list = [record.team.to_dict() for record in member_records if record.team]
    return jsonify(teams_list)


@teams_bp.route("/<int:team_id>", methods=["GET", "DELETE"])
@jwt_required()
def team_detail(team_id):
    """Get high-fidelity team metadata or delete the team if user is leader."""
    user_id = int(get_jwt_identity())
    team = Team.query.get_or_404(team_id)
    
    # Check membership
    membership = TeamMember.query.filter_by(team_id=team_id, user_id=user_id).first()
    if not membership:
        return jsonify({"error": "Access denied"}), 403
        
    if request.method == "DELETE":
        if team.created_by != user_id:
            return jsonify({"error": "Only the Team Leader can disband the team"}), 403
        db.session.delete(team)
        db.session.commit()
        return jsonify({"message": "Team successfully disbanded"})
        
    # GET: Detail including active projects and invitations
    data = team.to_dict()
    data["projects"] = [p.to_dict() for p in team.projects]
    data["invitations"] = [i.to_dict() for i in team.invitations if i.status == "pending"]
    return jsonify(data)


@teams_bp.route("/<int:team_id>/invite", methods=["POST"])
@jwt_required()
def invite_member(team_id):
    """Invite a peer student user to the collaborative team."""
    user_id = int(get_jwt_identity())
    team = Team.query.get_or_404(team_id)
    
    # Authorize sender (must be member)
    sender_mem = TeamMember.query.filter_by(team_id=team_id, user_id=user_id).first()
    if not sender_mem:
        return jsonify({"error": "Access denied"}), 403
        
    data = request.get_json() or {}
    email = sanitize_text(data.get("email", "")).strip()
    
    receiver = User.query.filter_by(email=email).first()
    if not receiver:
        return jsonify({"error": "Student user not found on campus"}), 404
        
    # Check if receiver is already a member
    existing_mem = TeamMember.query.filter_by(team_id=team_id, user_id=receiver.id).first()
    if existing_mem:
        return jsonify({"error": "User is already a member of this team"}), 400
        
    # Check existing pending invitations
    existing_inv = TeamInvitation.query.filter_by(team_id=team_id, receiver_id=receiver.id, status="pending").first()
    if existing_inv:
        return jsonify({"error": "An invitation is already pending for this user"}), 400
        
    inv = TeamInvitation(team_id=team_id, sender_id=user_id, receiver_id=receiver.id)
    db.session.add(inv)
    db.session.commit()
    
    # Notify Receiver
    sender_user = User.query.get(user_id)
    create_notification(
        user_id=receiver.id,
        title="👥 Team Invitation",
        message=f"{sender_user.full_name} invited you to join the team '{team.name}'.",
        ntype="info",
        link="/frontend/pages/student/workspace.html"
    )
    
    return jsonify(inv.to_dict()), 201


@teams_bp.route("/invitations", methods=["GET"])
@jwt_required()
def get_invitations():
    """Retrieve pending team invitations for the logged-in student."""
    user_id = int(get_jwt_identity())
    invs = TeamInvitation.query.filter_by(receiver_id=user_id, status="pending").all()
    return jsonify([i.to_dict() for i in invs])


@teams_bp.route("/invitations/<int:inv_id>", methods=["PUT"])
@jwt_required()
def handle_invitation(inv_id):
    """Accept or reject team collaborative invitations."""
    user_id = int(get_jwt_identity())
    inv = TeamInvitation.query.get_or_404(inv_id)
    
    if inv.receiver_id != user_id:
        return jsonify({"error": "Access denied"}), 403
        
    data = request.get_json() or {}
    action = sanitize_text(data.get("action", "")).lower() # accept or reject
    
    if action not in ("accept", "reject"):
        return jsonify({"error": "Action must be 'accept' or 'reject'"}), 400
        
    if action == "reject":
        inv.status = "rejected"
        db.session.commit()
        return jsonify({"message": "Invitation rejected"})
        
    # Accept: set status + add to TeamMember
    inv.status = "accepted"
    
    # Check double entry
    existing = TeamMember.query.filter_by(team_id=inv.team_id, user_id=user_id).first()
    if not existing:
        role = sanitize_text(data.get("role", "Frontend Developer"))
        member = TeamMember(team_id=inv.team_id, user_id=user_id, role=role)
        db.session.add(member)
        
    db.session.commit()
    
    # Notify team creator
    receiver_user = User.query.get(user_id)
    create_notification(
        user_id=inv.sender_id,
        title="✅ Invitation Accepted",
        message=f"{receiver_user.full_name} accepted your invitation to join '{inv.team.name}'!",
        ntype="success",
        link="/frontend/pages/student/workspace.html"
    )
    
    return jsonify({"message": "Invitation accepted successfully"})


@teams_bp.route("/<int:team_id>/members/<int:target_user_id>", methods=["DELETE"])
@jwt_required()
def remove_member(team_id, target_user_id):
    """Remove a student member from the collaborative group."""
    user_id = int(get_jwt_identity())
    team = Team.query.get_or_404(team_id)
    
    # Only team creator (Leader) can remove members, or user can self-leave
    if team.created_by != user_id and target_user_id != user_id:
        return jsonify({"error": "Unauthorized to remove members"}), 403
        
    member = TeamMember.query.filter_by(team_id=team_id, user_id=target_user_id).first_or_404()
    
    if team.created_by == target_user_id:
        return jsonify({"error": "Cannot remove the Team Leader/Creator"}), 400
        
    db.session.delete(member)
    db.session.commit()
    
    # Notify the user
    if target_user_id != user_id:
        create_notification(
            user_id=target_user_id,
            title="⚠️ Removed from Team",
            message=f"You have been removed from the team '{team.name}'.",
            ntype="warning"
        )
        
    return jsonify({"message": "Member removed successfully"})


@teams_bp.route("/<int:team_id>/members/<int:target_user_id>/role", methods=["PUT"])
@jwt_required()
def update_member_role(team_id, target_user_id):
    """Assign team roles (Leader, Frontend, Backend, UI/UX Designer, Researcher, Tester)."""
    user_id = int(get_jwt_identity())
    team = Team.query.get_or_404(team_id)
    
    # Only creator can assign roles
    if team.created_by != user_id:
        return jsonify({"error": "Only the Team Leader can assign roles"}), 403
        
    data = request.get_json() or {}
    role = sanitize_text(data.get("role", "")).strip()
    
    valid_roles = ["Team Leader", "Frontend Developer", "Backend Developer", "UI/UX Designer", "Researcher", "Tester"]
    if role not in valid_roles:
        return jsonify({"error": f"Invalid role. Must be one of: {', '.join(valid_roles)}"}), 400
        
    member = TeamMember.query.filter_by(team_id=team_id, user_id=target_user_id).first_or_404()
    member.role = role
    db.session.commit()
    
    # Notify Member
    create_notification(
        user_id=target_user_id,
        title="🎓 New Team Role Assigned",
        message=f"Your role in '{team.name}' has been updated to '{role}'.",
        ntype="info",
        link="/frontend/pages/student/workspace.html"
    )
    
    return jsonify(member.to_dict())


@teams_bp.route("/<int:team_id>/projects/<int:project_id>", methods=["POST"])
@jwt_required()
def assign_team_project(team_id, project_id):
    """Assign team ownership to an existing active freelance campaign."""
    user_id = int(get_jwt_identity())
    team = Team.query.get_or_404(team_id)
    project = Project.query.get_or_404(project_id)
    
    # Must be Team Leader and hired freelancer or client of the project
    if team.created_by != user_id:
        return jsonify({"error": "Only the Team Leader can claim project ownership"}), 403
        
    if project.hired_freelancer_id != user_id and project.client_id != user_id:
        return jsonify({"error": "You must be hired on this project to assign team ownership"}), 403
        
    project.team_id = team_id
    db.session.commit()
    
    # Notify all team members
    for m in team.members:
        if m.user_id != user_id:
            create_notification(
                user_id=m.user_id,
                title="💼 Team Project Assigned",
                message=f"Team '{team.name}' has taken ownership of project '{project.title}'. Let's collaborate!",
                ntype="success",
                link="/frontend/pages/student/workspace.html"
            )
            
    return jsonify(project.to_dict())


@teams_bp.route("/<int:team_id>/messages", methods=["GET"])
@jwt_required()
def get_team_messages(team_id):
    """Retrieve chat transcripts history for a team room workspace."""
    user_id = int(get_jwt_identity())
    
    # Check membership
    mem = TeamMember.query.filter_by(team_id=team_id, user_id=user_id).first()
    if not mem:
        return jsonify({"error": "Access denied"}), 403
        
    msgs = TeamMessage.query.filter_by(team_id=team_id).order_by(TeamMessage.created_at.asc()).limit(100).all()
    return jsonify([m.to_dict() for m in msgs])
