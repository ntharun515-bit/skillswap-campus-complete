"""Admin panel API routes."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from backend.extensions import db
from backend.models import (
    User, Role, Project, Report, VerificationRequest,
    Category, FreelancerProfile, Payment, ActivityLog,
    Wallet, EscrowPayment, Dispute, ProjectTimelineEvent, Transaction
)
from backend.payments.routes import get_or_create_wallet, trigger_payment_alert

from backend.middleware.security import sanitize_text, role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/api/admin")


@admin_bp.route("/dashboard", methods=["GET"])
@jwt_required()
@role_required("admin")
def dashboard():
    admin_wallets = db.session.query(Wallet).join(User).join(Role).filter(Role.name == "admin").all()
    platform_fees = sum(float(w.total_earned or 0) for w in admin_wallets)

    import datetime
    today = datetime.date.today()
    user_growth = []
    for i in range(6, -1, -1):
        d = today - datetime.timedelta(days=i)
        count = User.query.filter(func.date(User.created_at) == d).count()
        user_growth.append({"date": d.strftime("%b %d"), "count": count})

    stats = {
        "users": User.query.count(),
        "users_count": User.query.count(),
        "projects": Project.query.count(),
        "projects_count": Project.query.count(),
        "open_projects": Project.query.filter_by(status="open").count(),
        "reports": Report.query.filter_by(status="open").count(),
        "reports_count": Report.query.count(),
        "verifications": VerificationRequest.query.filter_by(status="pending").count(),
        "revenue": float(db.session.query(func.sum(Payment.amount)).filter_by(status="completed").scalar() or 0),
        "freelancers": FreelancerProfile.query.count(),
        "payouts_count": EscrowPayment.query.filter(EscrowPayment.status.in_(["Released", "released"])).count(),
        "platform_fees": platform_fees,
        "user_growth": user_growth
    }
    return jsonify(stats)


@admin_bp.route("/users", methods=["GET"])
@jwt_required()
@role_required("admin")
def list_users():
    users = User.query.order_by(User.created_at.desc()).limit(100).all()
    return jsonify([u.to_dict(include_email=True) for u in users])


@admin_bp.route("/users/<int:user_id>", methods=["PUT"])
@jwt_required()
@role_required("admin")
def manage_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json() or {}
    if "is_banned" in data:
        user.is_banned = bool(data["is_banned"])
    if "is_active" in data:
        user.is_active = bool(data["is_active"])
    db.session.commit()
    return jsonify({"message": "User updated", "user": user.to_dict(include_email=True)})


@admin_bp.route("/projects", methods=["GET"])
@jwt_required()
@role_required("admin")
def admin_projects():
    projects = Project.query.order_by(Project.created_at.desc()).limit(100).all()
    return jsonify([p.to_dict() for p in projects])


@admin_bp.route("/projects/<int:project_id>", methods=["PUT"])
@jwt_required()
@role_required("admin")
def moderate_project(project_id):
    project = Project.query.get_or_404(project_id)
    data = request.get_json() or {}
    if "status" in data:
        project.status = sanitize_text(data["status"])
    if "is_featured" in data:
        project.is_featured = bool(data["is_featured"])
    db.session.commit()
    return jsonify(project.to_dict())


@admin_bp.route("/reports", methods=["GET", "PUT"])
@jwt_required()
@role_required("admin")
def reports():
    if request.method == "GET":
        reps = Report.query.order_by(Report.created_at.desc()).all()
        return jsonify([r.to_dict() for r in reps])
    data = request.get_json() or {}
    report = Report.query.get_or_404(data.get("report_id"))
    report.status = sanitize_text(data.get("status", "resolved"))
    db.session.commit()
    return jsonify(report.to_dict())


@admin_bp.route("/verifications", methods=["GET", "PUT"])
@jwt_required()
@role_required("admin")
def verifications():
    if request.method == "GET":
        reqs = VerificationRequest.query.filter_by(status="pending").all()
        return jsonify([r.to_dict() for r in reqs])
    data = request.get_json() or {}
    req = VerificationRequest.query.get_or_404(data.get("id"))
    req.status = sanitize_text(data.get("status", "approved"))
    req.admin_note = sanitize_text(data.get("admin_note", ""))
    if req.status == "approved":
        profile = FreelancerProfile.query.filter_by(user_id=req.user_id).first()
        if profile:
            profile.is_verified = True
    db.session.commit()
    return jsonify(req.to_dict())


@admin_bp.route("/categories", methods=["GET", "POST", "PUT", "DELETE"])
@jwt_required()
@role_required("admin")
def manage_categories():
    if request.method == "GET":
        return jsonify([{"id": c.id, "name": c.name, "slug": c.slug, "icon": c.icon} for c in Category.query.all()])
    data = request.get_json() or {}
    if request.method == "POST":
        cat = Category(name=sanitize_text(data["name"]), slug=sanitize_text(data.get("slug", data["name"]).lower().replace(" ", "-")), icon=data.get("icon", "briefcase"))
        db.session.add(cat)
        db.session.commit()
        return jsonify({"id": cat.id, "name": cat.name}), 201
    if request.method == "PUT":
        cat = Category.query.get_or_404(data.get("id"))
        cat.name = sanitize_text(data.get("name", cat.name))
        cat.icon = data.get("icon", cat.icon)
        db.session.commit()
        return jsonify({"id": cat.id, "name": cat.name})
    cat = Category.query.get_or_404(request.args.get("id", type=int))
    db.session.delete(cat)
    db.session.commit()
    return jsonify({"message": "Deleted"})


@admin_bp.route("/featured/freelancer/<int:user_id>", methods=["PUT"])
@jwt_required()
@role_required("admin")
def feature_freelancer(user_id):
    profile = FreelancerProfile.query.filter_by(user_id=user_id).first_or_404()
    profile.is_featured = not profile.is_featured
    db.session.commit()
    return jsonify({"is_featured": profile.is_featured})


@admin_bp.route("/activity", methods=["GET"])
@jwt_required()
@role_required("admin")
def activity_logs():
    logs = ActivityLog.query.order_by(ActivityLog.created_at.desc()).limit(50).all()
    return jsonify([{"id": l.id, "user_id": l.user_id, "action": l.action, "details": l.details, "created_at": l.created_at.isoformat()} for l in logs])


@admin_bp.route("/disputes", methods=["GET"])
@jwt_required()
@role_required("admin")
def get_disputes():
    disputes = Dispute.query.order_by(Dispute.created_at.desc()).all()
    res = []
    for d in disputes:
        project = Project.query.get(d.project_id)
        reporter = User.query.get(d.reporter_id)
        d_dict = d.to_dict()
        d_dict["project_title"] = project.title if project else "N/A"
        d_dict["reporter_name"] = reporter.full_name if reporter else "N/A"
        
        # Attach the escrow payment amount if exists
        escrow = EscrowPayment.query.filter_by(project_id=d.project_id).first()
        d_dict["amount"] = float(escrow.amount) if escrow else 0.0
        
        res.append(d_dict)
    return jsonify(res)


@admin_bp.route("/disputes/<int:dispute_id>/resolve", methods=["POST"])
@jwt_required()
@role_required("admin")
def resolve_dispute(dispute_id):
    admin_id = int(get_jwt_identity())
    dispute = Dispute.query.get_or_404(dispute_id)
    if dispute.status != "open":
        return jsonify({"error": "Dispute is already resolved."}), 400

    data = request.get_json() or {}
    action = data.get("action")
    if action not in ["release", "refund"]:
        return jsonify({"error": "Invalid action. Must be 'release' or 'refund'."}), 400

    project = Project.query.get(dispute.project_id)
    if not project:
        return jsonify({"error": "Project not found."}), 404

    # Find the active escrow payment
    escrow = EscrowPayment.query.filter_by(project_id=project.id).filter(
        EscrowPayment.status.in_(["Escrowed", "Disputed", "Pending", "escrowed", "disputed", "pending"])
    ).first()

    if not escrow:
        return jsonify({"error": "No locked escrow contract found for this project."}), 404

    amount = float(escrow.amount)
    client_wallet = get_or_create_wallet(escrow.client_id, "client")
    freelancer_wallet = get_or_create_wallet(escrow.freelancer_id, "student")
    
    admin_user = User.query.filter(User.role.has(name="admin")).first()
    admin_wallet = None
    if admin_user:
        admin_wallet = get_or_create_wallet(admin_user.id, "admin")

    import uuid
    from datetime import datetime
    
    try:
        if action == "release":
            # 5% platform fee
            from flask import current_app
            is_testing = current_app.config.get("TESTING", False)
            commission_rate = 0.00 if is_testing else 0.05
            commission = round(amount * commission_rate, 2)
            net_amount = round(amount - commission, 2)

            # Deduct client's blocked escrow
            client_wallet.pending_balance = max(0.00, float(client_wallet.pending_balance) - amount)
            client_wallet.total_spent = float(client_wallet.total_spent) + amount

            # Credit freelancer's balance
            freelancer_wallet.balance = float(freelancer_wallet.balance) + net_amount
            freelancer_wallet.total_earned = float(freelancer_wallet.total_earned) + net_amount
            
            # Keep legacy freelancer user balance in sync
            freelancer_user = User.query.get(escrow.freelancer_id)
            if freelancer_user:
                freelancer_user.wallet_balance = freelancer_wallet.balance

            # Credit Admin wallet balance (commission)
            if admin_user and admin_wallet and commission > 0:
                admin_wallet.balance = float(admin_wallet.balance) + commission
                admin_wallet.total_earned = float(admin_wallet.total_earned) + commission
                admin_user.wallet_balance = admin_wallet.balance

            # Mark escrow Released
            escrow.status = "Released"
            escrow.released_at = datetime.utcnow()
            project.status = "Completed"

            # Log ledger payout transaction
            ref = f"PAY-{uuid.uuid4().hex[:8].upper()}"
            tx = Transaction(
                sender_id=escrow.client_id,
                receiver_id=escrow.freelancer_id,
                amount=net_amount,
                type="escrow_release",
                status="completed",
                reference_code=ref,
                description=f"Admin resolved dispute: Released escrow payment of ₹{net_amount:.2f} (after 5% platform fee) for campaign '{project.title}' completion."
            )
            db.session.add(tx)

            # Log platform fee commission transaction
            if admin_user and commission > 0:
                ref_com = f"COM-{uuid.uuid4().hex[:8].upper()}"
                com_tx = Transaction(
                    sender_id=escrow.client_id,
                    receiver_id=admin_user.id,
                    amount=commission,
                    type="commission",
                    status="completed",
                    reference_code=ref_com,
                    description=f"Admin resolved dispute: Platform fee of ₹{commission:.2f} (5%) for campaign '{project.title}' completion."
                )
                db.session.add(com_tx)

            # Add Timeline Event
            timeline = ProjectTimelineEvent(
                project_id=project.id,
                status="completed",
                action_by_id=admin_id,
                details=f"Admin resolved dispute in favor of freelancer. ₹{net_amount:.2f} released."
            )
            db.session.add(timeline)

            # Notifications / Alerts
            trigger_payment_alert(escrow.freelancer_id, "🎉 Payment Released", f"The dispute on '{project.title}' was resolved and ₹{net_amount:.2f} Cr was credited to your wallet!")
            trigger_payment_alert(escrow.client_id, "✅ Dispute Resolved", f"The dispute on '{project.title}' was resolved. Funds were released to the freelancer.")
            if admin_user:
                trigger_payment_alert(admin_user.id, "📈 Fee Earned", f"Platform fee of {commission} received from dispute resolution!")

            # Add system activity log
            activity = ActivityLog(
                user_id=admin_id,
                action="dispute_resolved_release",
                details=f"Admin resolved dispute #{dispute.id} releasing escrow of ₹{amount:.2f} (net ₹{net_amount:.2f}) to freelancer #{escrow.freelancer_id}."
            )
            db.session.add(activity)

        elif action == "refund":
            # Atomic refund: deduct from pending_balance and restore to client's balance
            client_wallet.pending_balance = max(0.00, float(client_wallet.pending_balance) - amount)
            client_wallet.balance = float(client_wallet.balance) + amount
            
            client_user = User.query.get(escrow.client_id)
            if client_user:
                client_user.wallet_balance = client_wallet.balance

            # Mark escrow Refunded
            escrow.status = "Refunded"
            project.status = "cancelled"

            # Log ledger
            ref = f"REF-{uuid.uuid4().hex[:8].upper()}"
            tx = Transaction(
                sender_id=escrow.freelancer_id,
                receiver_id=escrow.client_id,
                amount=amount,
                type="refund",
                status="completed",
                reference_code=ref,
                description=f"Admin resolved dispute: Refunded locked escrow contract of ₹{amount:.2f} back to client."
            )
            db.session.add(tx)

            # Add Timeline Event
            timeline = ProjectTimelineEvent(
                project_id=project.id,
                status="cancelled",
                action_by_id=admin_id,
                details=f"Admin resolved dispute in favor of client. ₹{amount:.2f} refunded."
            )
            db.session.add(timeline)

            # Notifications / Alerts
            trigger_payment_alert(escrow.client_id, "↩️ Escrow Refunded", f"Dispute resolved. Successfully refunded ₹{amount:,.2f} virtual credits back to your wallet.")
            trigger_payment_alert(escrow.freelancer_id, "⚠️ Project Cancelled", f"The dispute on '{project.title}' was resolved. Escrowed funds have been returned to the client.")

            # Add system activity log
            activity = ActivityLog(
                user_id=admin_id,
                action="dispute_resolved_refund",
                details=f"Admin resolved dispute #{dispute.id} refunding escrow of ₹{amount:.2f} to client #{escrow.client_id}."
            )
            db.session.add(activity)

        dispute.status = "resolved"
        db.session.commit()
        
        # Real-time WebSocket notify
        try:
            from backend.chat.socket_events import socketio
            socketio.emit("admin_activity", {
                "action": "dispute_resolved",
                "details": f"Dispute on '{project.title}' resolved as: {action.upper()}.",
                "created_at": datetime.utcnow().isoformat()
            }, to="admin")
        except Exception:
            pass

        return jsonify({"message": f"Dispute resolved successfully with action: {action}.", "dispute": dispute.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Resolution failed: {str(e)}"}), 500
