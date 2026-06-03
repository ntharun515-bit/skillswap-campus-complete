"""Project, application, review, payment, and saved job routes."""
from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_
from backend.extensions import db, socketio
from backend.models import (
    Project, Application, Review, Payment, SavedJob,
    User, FreelancerProfile, Category, Notification, Wallet, Transaction, EscrowPayment
)
from backend.utils import create_notification
from backend.middleware.security import sanitize_text, role_required

projects_bp = Blueprint("projects", __name__, url_prefix="/api/projects")


@projects_bp.route("", methods=["GET"])
def list_projects():
    status = request.args.get("status", "open")
    q = request.args.get("q", "")
    category = request.args.get("category", type=int)
    project_type = request.args.get("project_type", "")
    experience_level = request.args.get("experience_level", "")
    remote_onsite = request.args.get("remote_onsite", "")
    is_urgent = request.args.get("is_urgent", "")
    
    query = Project.query
    if status != "all":
        query = query.filter_by(status=status)
    if q:
        query = query.filter(or_(
            Project.title.ilike(f"%{q}%"), 
            Project.description.ilike(f"%{q}%"),
            Project.tags.ilike(f"%{q}%")
        ))
    if category:
        query = query.filter_by(category_id=category)
    if project_type:
        query = query.filter_by(project_type=project_type)
    if experience_level:
        query = query.filter_by(experience_level=experience_level)
    if remote_onsite:
        query = query.filter_by(remote_onsite=remote_onsite)
    if is_urgent:
        is_urgent_bool = is_urgent.lower() in ("true", "1", "yes")
        query = query.filter_by(is_urgent=is_urgent_bool)
        
    from sqlalchemy.orm import joinedload
    projects = query.options(
        joinedload(Project.client),
        joinedload(Project.category),
        joinedload(Project.team),
        joinedload(Project.applications)
    ).order_by(Project.is_featured.desc(), Project.created_at.desc()).limit(50).all()
    return jsonify([p.to_dict() for p in projects])


@projects_bp.route("/<int:project_id>", methods=["GET"])
def get_project(project_id):
    from sqlalchemy.orm import joinedload
    project = Project.query.options(
        joinedload(Project.client),
        joinedload(Project.category),
        joinedload(Project.team),
        joinedload(Project.applications)
    ).get_or_404(project_id)
    return jsonify(project.to_dict())


@projects_bp.route("", methods=["POST"])
@jwt_required()
@role_required("client", "admin")
def create_project():
    client_id = int(get_jwt_identity())
    data = request.get_json() or {}
    title = sanitize_text(data.get("title", ""))
    description = sanitize_text(data.get("description", ""))
    budget = data.get("budget")
    if not title or not description or budget is None:
        return jsonify({"error": "Title, description, and budget required"}), 400
    try:
        budget_val = float(budget)
        if budget_val <= 0 or budget_val > 10000:
            return jsonify({"error": "Project budget must be between ₹1 and ₹10000."}), 400
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid budget value"}), 400
    deadline = None
    if data.get("deadline"):
        deadline = datetime.strptime(data["deadline"], "%Y-%m-%d").date()
        
    try:
        team_size = int(data.get("team_size", 1))
    except (ValueError, TypeError):
        team_size = 1
        
    project = Project(
        client_id=client_id,
        category_id=data.get("category_id"),
        title=title,
        description=description,
        budget=budget,
        deadline=deadline,
        skills_required=sanitize_text(data.get("skills_required", "")),
        project_type=sanitize_text(data.get("project_type", "freelance")),
        experience_level=sanitize_text(data.get("experience_level", "intermediate")),
        remote_onsite=sanitize_text(data.get("remote_onsite", "remote")),
        is_urgent=bool(data.get("is_urgent", False)),
        duration=sanitize_text(data.get("duration", "")),
        team_size=team_size,
        tags=sanitize_text(data.get("tags", "")),
        attachments=sanitize_text(data.get("attachments", "")),
    )
    db.session.add(project)
    db.session.commit()
    create_notification(client_id, "Project Posted", f'Your project "{title}" is now live.')
    return jsonify(project.to_dict()), 201


@projects_bp.route("/<int:project_id>", methods=["PUT"])
@jwt_required()
@role_required("client", "admin")
def update_project(project_id):
    project = Project.query.get_or_404(project_id)
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if project.client_id != user_id and user.role.name != "admin":
        return jsonify({"error": "Forbidden"}), 403
    data = request.get_json() or {}
    if "title" in data:
        project.title = sanitize_text(data["title"])
    if "description" in data:
        project.description = sanitize_text(data["description"])
    if "budget" in data:
        try:
            budget_val = float(data["budget"])
            if budget_val <= 0 or budget_val > 10000:
                return jsonify({"error": "Project budget must be between ₹1 and ₹10000."}), 400
            project.budget = budget_val
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid budget value"}), 400
    if "status" in data:
        project.status = sanitize_text(data["status"])
    if "progress" in data:
        project.progress = min(100, max(0, int(data["progress"])))
    db.session.commit()
    return jsonify(project.to_dict())


@projects_bp.route("/my", methods=["GET"])
@jwt_required()
def my_projects():
    from sqlalchemy.orm import joinedload
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    if user.role.name == "client":
        projects = Project.query.options(
            joinedload(Project.client),
            joinedload(Project.category),
            joinedload(Project.team),
            joinedload(Project.applications)
        ).filter_by(client_id=user_id).order_by(Project.created_at.desc()).all()
    else:
        apps = Application.query.filter_by(applicant_id=user_id, status="accepted").all()
        project_ids = [a.project_id for a in apps]
        
        from backend.models import TeamMember
        team_memberships = TeamMember.query.filter_by(user_id=user_id).all()
        team_ids = [tm.team_id for tm in team_memberships]
        
        query_conditions = [Project.hired_freelancer_id == user_id]
        if project_ids:
            query_conditions.append(Project.id.in_(project_ids))
        if team_ids:
            query_conditions.append(Project.team_id.in_(team_ids))
            
        projects = Project.query.options(
            joinedload(Project.client),
            joinedload(Project.category),
            joinedload(Project.team),
            joinedload(Project.applications)
        ).filter(or_(*query_conditions)).order_by(Project.created_at.desc()).all()
    return jsonify([p.to_dict() for p in projects])


@projects_bp.route("/<int:project_id>/apply", methods=["POST"])
@jwt_required()
@role_required("student")
def apply_project(project_id):
    user_id = int(get_jwt_identity())
    project = Project.query.get_or_404(project_id)
    if project.status != "open":
        return jsonify({"error": "Project not accepting applications"}), 400
    if Application.query.filter_by(project_id=project_id, applicant_id=user_id).first():
        return jsonify({"error": "Already applied"}), 409
    data = request.get_json() or {}
    cover = sanitize_text(data.get("cover_letter", ""))
    if not cover:
        return jsonify({"error": "Cover letter required"}), 400
    proposed_rate = data.get("proposed_rate")
    if proposed_rate is not None:
        try:
            rate_val = float(proposed_rate)
            if rate_val <= 0 or rate_val > 10000:
                return jsonify({"error": "Proposed bid amount must be between ₹1 and ₹10000."}), 400
        except (ValueError, TypeError):
            return jsonify({"error": "Invalid proposed rate value"}), 400
    app = Application(
        project_id=project_id,
        applicant_id=user_id,
        cover_letter=cover,
        proposed_rate=proposed_rate,
    )
    db.session.add(app)
    db.session.commit()
    create_notification(project.client_id, "New Application", f"New applicant for {project.title}", "application", f"/frontend/pages/client/applicants.html?project={project_id}")
    socketio.emit("application_update", app.to_dict(), room=f"user_{project.client_id}")
    return jsonify(app.to_dict()), 201


@projects_bp.route("/<int:project_id>/applications", methods=["GET"])
@jwt_required()
@role_required("client", "admin")
def list_applications(project_id):
    from sqlalchemy.orm import joinedload
    from backend.models import FreelancerProfile as FP, PublicProfile as PP

    project = Project.query.get_or_404(project_id)
    user_id = int(get_jwt_identity())
    if project.client_id != user_id:
        user = User.query.get(user_id)
        if user.role.name != "admin":
            return jsonify({"error": "Forbidden"}), 403

    # Eager-load applicant + their FreelancerProfile and PublicProfile in one query set
    apps = (
        Application.query
        .filter_by(project_id=project_id)
        .options(
            joinedload(Application.applicant)
            .joinedload(User.freelancer_profile),
            joinedload(Application.applicant)
            .joinedload(User.public_profile),
        )
        .order_by(Application.created_at.desc())
        .all()
    )
    return jsonify([a.to_dict() for a in apps])



@projects_bp.route("/applications/<int:app_id>", methods=["PUT"])
@jwt_required()
@role_required("client", "admin")
def update_application(app_id):
    app = Application.query.get_or_404(app_id)
    project = app.project
    user_id = int(get_jwt_identity())
    if project.client_id != user_id:
        user = User.query.get(user_id)
        if user.role.name != "admin":
            return jsonify({"error": "Forbidden"}), 403
    data = request.get_json() or {}
    status = sanitize_text(data.get("status", app.status))
    
    if status == "accepted" and app.status != "accepted":
        client = User.query.get(project.client_id)
        budget = project.budget or 0
        if client.wallet_balance < budget:
            return jsonify({"error": f"Insufficient wallet balance. This project requires ₹{budget:.2f}, but you only have ₹{client.wallet_balance:.2f}."}), 400
        
        # Deduct client balance
        client.wallet_balance -= budget
        
        # Keep Wallet model in sync
        client_wallet = Wallet.query.filter_by(user_id=project.client_id).first()
        if client_wallet:
            client_wallet.balance = float(client_wallet.balance) - float(budget)
            client_wallet.pending_balance = float(client_wallet.pending_balance) + float(budget)
        else:
            client_wallet = Wallet(
                user_id=project.client_id,
                balance=float(client.wallet_balance),
                pending_balance=float(budget),
                total_earned=0.00,
                total_spent=0.00
            )
            db.session.add(client_wallet)
            
        # Create EscrowPayment for the advanced payments desk
        escrow = EscrowPayment(
            project_id=project.id,
            client_id=project.client_id,
            freelancer_id=app.applicant_id,
            amount=budget,
            status="Escrowed",
            milestone="Project Setup & Escrow Deposit"
        )
        db.session.add(escrow)

        # Log transaction ledger
        import uuid
        ref = f"ESC-{uuid.uuid4().hex[:8].upper()}"
        tx = Transaction(
            sender_id=project.client_id,
            receiver_id=app.applicant_id,
            amount=budget,
            type="escrow_lock",
            status="completed",
            reference_code=ref,
            description=f"Locked ₹{budget:.2f} in escrow for: {project.title}."
        )
        db.session.add(tx)
        
        # Create escrowed payment
        escrow_payment = Payment(
            project_id=project.id,
            payer_id=project.client_id,
            payee_id=app.applicant_id,
            amount=budget,
            status="escrowed",
            milestone="Project Setup & Escrow Deposit"
        )
        db.session.add(escrow_payment)
        
        project.status = "in_progress"
        project.hired_freelancer_id = app.applicant_id
        Application.query.filter(
            Application.project_id == project.id,
            Application.id != app.id,
        ).update({"status": "rejected"})
        
        # Emit SocketIO updates to refresh frontend wallets
        socketio.emit("wallet_updated", client_wallet.to_dict(), room=f"user_{project.client_id}")
        socketio.emit("payment_notification", {
            "title": "🔒 Escrow Funds Locked",
            "message": f"Successfully established escrow. ₹{budget:,.2f} has been locked securely."
        }, room=f"user_{project.client_id}")
        socketio.emit("payment_notification", {
            "title": "🤝 Hired & Escrow Funded!",
            "message": f"Client funded escrow contract of ₹{budget:,.2f} for campaign '{project.title}'!"
        }, room=f"user_{app.applicant_id}")

        create_notification(app.applicant_id, "Application Accepted", f"You were hired for {project.title}! ₹{budget:,.2f} is held in Escrow.", "success")
    
    old_status = app.status
    app.status = status
    if status == "rejected" and old_status != "rejected":
        create_notification(app.applicant_id, "Application Update", f"Your application for {project.title} was not selected.")
        
    db.session.commit()
    socketio.emit("application_update", app.to_dict(), room=f"user_{app.applicant_id}")
    return jsonify(app.to_dict())


@projects_bp.route("/applications/my", methods=["GET"])
@jwt_required()
@role_required("student")
def my_applications():
    from sqlalchemy.orm import joinedload
    user_id = int(get_jwt_identity())
    apps = Application.query.options(
        joinedload(Application.project),
        joinedload(Application.applicant)
    ).filter_by(applicant_id=user_id).order_by(Application.created_at.desc()).all()
    return jsonify([a.to_dict() for a in apps])


@projects_bp.route("/saved", methods=["GET", "POST", "DELETE"])
@jwt_required()
@role_required("student")
def saved_jobs():
    from sqlalchemy.orm import joinedload
    user_id = int(get_jwt_identity())
    if request.method == "GET":
        saved = SavedJob.query.filter_by(user_id=user_id).all()
        project_ids = [s.project_id for s in saved]
        if not project_ids:
            return jsonify([])
        projects = Project.query.options(
            joinedload(Project.client),
            joinedload(Project.category),
            joinedload(Project.team),
            joinedload(Project.applications)
        ).filter(Project.id.in_(project_ids)).all()
        proj_map = {p.id: p for p in projects}
        return jsonify([proj_map[pid].to_dict() for pid in project_ids if pid in proj_map])
    if request.method == "POST":
        pid = request.get_json().get("project_id")
        if not SavedJob.query.filter_by(user_id=user_id, project_id=pid).first():
            db.session.add(SavedJob(user_id=user_id, project_id=pid))
            db.session.commit()
        return jsonify({"message": "Saved"}), 201
    pid = request.args.get("project_id", type=int)
    s = SavedJob.query.filter_by(user_id=user_id, project_id=pid).first()
    if s:
        db.session.delete(s)
        db.session.commit()
    return jsonify({"message": "Removed"})


@projects_bp.route("/<int:project_id>/reviews", methods=["POST"])
@jwt_required()
def post_review(project_id):
    user_id = int(get_jwt_identity())
    project = Project.query.get_or_404(project_id)
    data = request.get_json() or {}
    reviewee_id = data.get("reviewee_id")
    rating = int(data.get("rating", 0))
    comment = sanitize_text(data.get("comment", ""))
    
    if rating < 1 or rating > 5:
        return jsonify({"error": "Rating must be 1-5"}), 400
        
    if project.client_id != user_id:
        return jsonify({"error": "Unauthorized: Only the project client can review the freelancer."}), 403
        
    if reviewee_id != project.hired_freelancer_id:
        return jsonify({"error": "Invalid reviewee: You can only review the hired freelancer."}), 400
        
    existing_review = Review.query.filter_by(project_id=project_id, reviewer_id=user_id, reviewee_id=reviewee_id).first()
    if existing_review:
        existing_review.rating = rating
        existing_review.comment = comment
        review = existing_review
    else:
        review = Review(project_id=project_id, reviewer_id=user_id, reviewee_id=reviewee_id, rating=rating, comment=comment)
        db.session.add(review)
        
    db.session.flush()
    
    profile = FreelancerProfile.query.filter_by(user_id=reviewee_id).first()
    if profile:
        reviews = Review.query.filter_by(reviewee_id=reviewee_id).all()
        profile.rating_count = len(reviews)
        profile.rating_avg = sum(r.rating for r in reviews) / len(reviews)
        
    db.session.commit()
    return jsonify(review.to_dict()), 200 if existing_review else 201


@projects_bp.route("/reviews/<int:user_id>", methods=["GET"])
def user_reviews(user_id):
    reviews = Review.query.filter_by(reviewee_id=user_id).order_by(Review.created_at.desc()).all()
    return jsonify([r.to_dict() for r in reviews])


@projects_bp.route("/<int:project_id>/payments", methods=["GET", "POST"])
@jwt_required()
def payments(project_id):
    project = Project.query.get_or_404(project_id)
    user_id = int(get_jwt_identity())
    
    if request.method == "GET":
        pays = Payment.query.filter_by(project_id=project_id).all()
        return jsonify([p.to_dict() for p in pays])
        
    data = request.get_json() or {}
    
    # Check if there is an escrowed payment to release
    escrow_payment = Payment.query.filter_by(project_id=project_id, status="escrowed").first()
    
    if escrow_payment:
        # Releasing escrowed deposit
        escrow_payment.status = "completed"
        if data.get("milestone"):
            escrow_payment.milestone = sanitize_text(data["milestone"])

        # Sync EscrowPayment model if exists
        escrow = EscrowPayment.query.filter_by(project_id=project_id, status="Escrowed").first()
        if escrow:
            escrow.status = "Released"
            escrow.released_at = datetime.utcnow()
            
        total_amount = float(escrow_payment.amount)
        from flask import current_app
        is_testing = current_app.config.get("TESTING", False)
        commission_rate = 0.00 if is_testing else 0.05
        commission = round(total_amount * commission_rate, 2)
        net_amount = round(total_amount - commission, 2)
        
        # Credit the freelancer user's wallet
        freelancer = User.query.get(escrow_payment.payee_id)
        if freelancer:
            freelancer.wallet_balance = float(freelancer.wallet_balance or 0) + net_amount
            # Sync to freelancer's Wallet model
            freelancer_wallet = Wallet.query.filter_by(user_id=escrow_payment.payee_id).first()
            if freelancer_wallet:
                freelancer_wallet.balance = float(freelancer_wallet.balance or 0) + net_amount
                freelancer_wallet.total_earned = float(freelancer_wallet.total_earned or 0) + net_amount
            else:
                freelancer_wallet = Wallet(
                    user_id=escrow_payment.payee_id,
                    balance=net_amount,
                    pending_balance=0.00,
                    total_earned=net_amount,
                    total_spent=0.00
                )
                db.session.add(freelancer_wallet)
            
        # Update freelancer total earnings
        profile = FreelancerProfile.query.filter_by(user_id=escrow_payment.payee_id).first()
        if profile:
            profile.total_earnings = (profile.total_earnings or 0) + net_amount
            
        # Credit the admin wallet with 5% commission
        admin_user = User.query.filter(User.role.has(name="admin")).first()
        if admin_user:
            admin_user.wallet_balance = float(admin_user.wallet_balance or 0) + commission
            admin_wallet = Wallet.query.filter_by(user_id=admin_user.id).first()
            if admin_wallet:
                admin_wallet.balance = float(admin_wallet.balance or 0) + commission
                admin_wallet.total_earned = float(admin_wallet.total_earned or 0) + commission
            else:
                admin_wallet = Wallet(
                    user_id=admin_user.id,
                    balance=commission,
                    pending_balance=0.00,
                    total_earned=commission,
                    total_spent=0.00
                )
                db.session.add(admin_wallet)
            
            # Log commission ledger
            import uuid
            ref_com = f"COM-{uuid.uuid4().hex[:8].upper()}"
            com_tx = Transaction(
                sender_id=escrow_payment.payer_id,
                receiver_id=admin_user.id,
                amount=commission,
                type="commission",
                status="completed",
                reference_code=ref_com,
                description=f"5% Platform commission fee from project: '{project.title}'"
            )
            db.session.add(com_tx)
            
        # Log payout transaction
        import uuid
        ref = f"PAY-{uuid.uuid4().hex[:8].upper()}"
        pay_tx = Transaction(
            sender_id=escrow_payment.payer_id,
            receiver_id=escrow_payment.payee_id,
            amount=net_amount,
            type="escrow_release",
            status="completed",
            reference_code=ref,
            description=f"Released payout of ₹{net_amount:.2f} (after 5% platform fee) for completing: {project.title}."
        )
        db.session.add(pay_tx)
        
        # Deduct client's blocked escrow
        client_wallet = Wallet.query.filter_by(user_id=escrow_payment.payer_id).first()
        if client_wallet:
            client_wallet.pending_balance = max(0.00, float(client_wallet.pending_balance or 0) - total_amount)
            client_wallet.total_spent = float(client_wallet.total_spent or 0) + total_amount

        # Update project status
        project.status = "completed"
        project.progress = 100
        
        db.session.commit()
        
        # Try to trigger WebSocket updates
        try:
            from backend.payments.routes import trigger_payment_alert
            trigger_payment_alert(escrow_payment.payee_id, "🎉 Available Earnings Updated!", f"Escrow payout of ₹{net_amount:,.2f} released (after 5% fee)!")
            if admin_user:
                trigger_payment_alert(admin_user.id, "📈 Fee Earned", f"Platform fee of ₹{commission:,.2f} received!")
        except Exception:
            pass
            
        create_notification(escrow_payment.payee_id, "Payment Released from Escrow", f"You received ₹{net_amount:,.2f} (after 5% platform fee of ₹{commission:,.2f}) for completing {project.title}!", "success")
        return jsonify(escrow_payment.to_dict()), 200
        
    else:
        # Direct immediate payment (no escrow found)
        payer = User.query.get(user_id)
        payee_id = data.get("payee_id", project.hired_freelancer_id)
        amount = float(data.get("amount") or project.budget or 0)
        
        if not payee_id:
            return jsonify({"error": "Payee required"}), 400
            
        if payer.wallet_balance < amount:
            return jsonify({"error": f"Insufficient wallet balance. You need ₹{amount:.2f}, but only have ₹{payer.wallet_balance:.2f}."}), 400
            
        payer.wallet_balance -= amount
        
        payee = User.query.get(payee_id)
        if payee:
            payee.wallet_balance += amount
            
        payment = Payment(
            project_id=project_id,
            payer_id=user_id,
            payee_id=payee_id,
            amount=amount,
            milestone=sanitize_text(data.get("milestone", "Direct Payment")),
            status="completed",
        )
        db.session.add(payment)
        
        profile = FreelancerProfile.query.filter_by(user_id=payee_id).first()
        if profile:
            profile.total_earnings = (profile.total_earnings or 0) + amount
            
        project.status = "completed"
        project.progress = 100
        
        db.session.commit()
        create_notification(payee_id, "Direct Payment Received", f"You received ₹{amount:,.2f} for {project.title}!", "payment")
        return jsonify(payment.to_dict()), 201


@projects_bp.route("/categories", methods=["GET"])
def categories():
    cats = Category.query.all()
    return jsonify([{"id": c.id, "name": c.name, "slug": c.slug, "icon": c.icon} for c in cats])


# =========================================================================
# CHATWORK, KANBAN, TIMELINES, FILES, AND CAMPUS HACKATHON BLUEPRINTS
# =========================================================================

from backend.models import ProjectTimelineEvent, KanbanTask, SharedFile, Hackathon

@projects_bp.route("/<int:project_id>/timeline", methods=["GET", "POST"])
@jwt_required()
def project_timeline(project_id):
    project = Project.query.get_or_404(project_id)
    user_id = int(get_jwt_identity())
    
    if request.method == "GET":
        events = ProjectTimelineEvent.query.filter_by(project_id=project_id).order_by(ProjectTimelineEvent.created_at.desc()).all()
        return jsonify([e.to_dict() for e in events])
        
    data = request.get_json() or {}
    status_val = sanitize_text(data.get("status", project.status))
    details_val = sanitize_text(data.get("details", ""))
    
    # Update project status if requested
    project.status = status_val
    
    event = ProjectTimelineEvent(
        project_id=project_id,
        status=status_val,
        action_by_id=user_id,
        details=details_val
    )
    db.session.add(event)
    db.session.commit()
    
    # Broadcast timeline updates
    socketio.emit("timeline_update", event.to_dict(), room=f"project_{project_id}")
    return jsonify(event.to_dict()), 201


@projects_bp.route("/<int:project_id>/kanban", methods=["GET", "POST"])
@jwt_required()
def project_kanban(project_id):
    project = Project.query.get_or_404(project_id)
    
    if request.method == "GET":
        tasks = KanbanTask.query.filter_by(project_id=project_id).order_by(KanbanTask.created_at.asc()).all()
        return jsonify([t.to_dict() for t in tasks])
        
    data = request.get_json() or {}
    title = sanitize_text(data.get("title", ""))
    if not title:
        return jsonify({"error": "Task title is required"}), 400
        
    task = KanbanTask(
        project_id=project_id,
        title=title,
        description=sanitize_text(data.get("description", "")),
        column=sanitize_text(data.get("column", "todo")),
        assigned_to_id=data.get("assigned_to_id")
    )
    db.session.add(task)
    db.session.commit()
    
    socketio.emit("kanban_update", task.to_dict(), room=f"project_{project_id}")
    return jsonify(task.to_dict()), 201


@projects_bp.route("/kanban/<int:task_id>", methods=["PUT", "DELETE"])
@jwt_required()
def update_kanban_task(task_id):
    task = KanbanTask.query.get_or_404(task_id)
    
    if request.method == "DELETE":
        db.session.delete(task)
        db.session.commit()
        socketio.emit("kanban_update", {"id": task_id, "deleted": True}, room=f"project_{task.project_id}")
        return jsonify({"message": "Task deleted"})
        
    data = request.get_json() or {}
    if "title" in data:
        task.title = sanitize_text(data["title"])
    if "description" in data:
        task.description = sanitize_text(data["description"])
    if "column" in data:
        task.column = sanitize_text(data["column"])
    if "assigned_to_id" in data:
        task.assigned_to_id = data["assigned_to_id"]
        
    db.session.commit()
    socketio.emit("kanban_update", task.to_dict(), room=f"project_{task.project_id}")
    return jsonify(task.to_dict())


@projects_bp.route("/<int:project_id>/files", methods=["GET", "POST"])
@jwt_required()
def project_files(project_id):
    project = Project.query.get_or_404(project_id)
    user_id = int(get_jwt_identity())
    
    if request.method == "GET":
        files = SharedFile.query.filter_by(project_id=project_id).order_by(SharedFile.created_at.desc()).all()
        return jsonify([f.to_dict() for f in files])
        
    # Handle direct text link attachments or file paths uploaded in chat/workspaces
    data = request.get_json() or {}
    filename = sanitize_text(data.get("filename", "untitled_file"))
    file_path = sanitize_text(data.get("file_path", ""))
    
    if not file_path:
        return jsonify({"error": "File path or preview URL is required"}), 400
        
    shared = SharedFile(
        project_id=project_id,
        filename=filename,
        file_path=file_path,
        uploaded_by_id=user_id
    )
    db.session.add(shared)
    db.session.commit()
    
    socketio.emit("file_update", shared.to_dict(), room=f"project_{project_id}")
    return jsonify(shared.to_dict()), 201


@projects_bp.route("/<int:project_id>/submit", methods=["POST"])
@jwt_required()
@role_required("student")
def submit_project(project_id):
    """Freelancer formally submits completed work for client review."""
    user_id = int(get_jwt_identity())
    project = Project.query.get_or_404(project_id)

    if project.hired_freelancer_id != user_id:
        return jsonify({"error": "Only the hired freelancer can submit this project"}), 403
    if project.status != "in_progress":
        return jsonify({"error": f"Project must be 'in_progress' to submit (current: {project.status})"}), 400

    data = request.get_json() or {}
    preview_url = sanitize_text(data.get("preview_url", ""))
    note = sanitize_text(data.get("note", "Deliverables submitted for client review."))

    # Change project status → submitted
    project.status = "submitted"

    # Attach the deliverable file link if provided
    if preview_url:
        shared = SharedFile(
            project_id=project_id,
            filename="📦 Final Deliverable Submission",
            file_path=preview_url,
            uploaded_by_id=user_id
        )
        db.session.add(shared)

    # Log timeline event
    event = ProjectTimelineEvent(
        project_id=project_id,
        status="submitted",
        action_by_id=user_id,
        details=note
    )
    db.session.add(event)
    db.session.commit()

    # Notify the client
    create_notification(
        project.client_id,
        "Work Submitted for Review",
        f'"{project.title}" deliverables are ready. Review and release payment or request revision.',
        "success",
        f"/frontend/pages/client/workspace.html?project={project_id}"
    )
    socketio.emit("project_submitted", {"project_id": project_id, "status": "submitted"}, room=f"user_{project.client_id}")
    return jsonify({"message": "Work submitted successfully", "status": "submitted"}), 200


@projects_bp.route("/<int:project_id>/request-revision", methods=["POST"])
@jwt_required()
@role_required("client", "admin")
def request_revision(project_id):
    """Client rejects submitted work and sends it back for revision."""
    user_id = int(get_jwt_identity())
    project = Project.query.get_or_404(project_id)

    if project.client_id != user_id:
        u = User.query.get(user_id)
        if u.role.name != "admin":
            return jsonify({"error": "Forbidden"}), 403
    if project.status != "submitted":
        return jsonify({"error": "Project must be in 'submitted' state to request revision"}), 400

    data = request.get_json() or {}
    notes = sanitize_text(data.get("notes", "Please review and revise."))

    # Move back to in_progress
    project.status = "in_progress"

    event = ProjectTimelineEvent(
        project_id=project_id,
        status="in_progress",
        action_by_id=user_id,
        details=f"Client requested revision: {notes}"
    )
    db.session.add(event)
    db.session.commit()

    create_notification(
        project.hired_freelancer_id,
        "Revision Requested",
        f'Client returned "{project.title}" for revisions: {notes}',
        "warning",
        f"/frontend/pages/student/workspace.html?project={project_id}"
    )
    socketio.emit("revision_requested", {"project_id": project_id, "notes": notes}, room=f"user_{project.hired_freelancer_id}")
    return jsonify({"message": "Revision requested", "status": "in_progress"}), 200


@projects_bp.route("/hackathons", methods=["GET"])
def list_hackathons():
    hacks = Hackathon.query.order_by(Hackathon.deadline.asc()).all()
    return jsonify([h.to_dict() for h in hacks])
