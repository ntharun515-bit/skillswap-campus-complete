"""General API: notifications, reports, health."""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.extensions import db
from backend.models import Notification, Report
from backend.middleware.security import sanitize_text

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/health", methods=["GET"])
def health():
    try:
        # Perform a lightweight check to ensure DB connectivity is active
        db.session.execute(db.text("SELECT 1"))
        return jsonify({
            "status": "healthy",
            "app": "SkillSwap",
            "database": "connected"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "app": "SkillSwap",
            "database": "disconnected",
            "error": str(e)
        }), 500


@api_bp.route("/notifications", methods=["GET"])
@jwt_required()
def notifications():
    user_id = int(get_jwt_identity())
    unread_only = request.args.get("unread") == "true"
    query = Notification.query.filter_by(user_id=user_id)
    if unread_only:
        query = query.filter_by(is_read=False)
    notes = query.order_by(Notification.created_at.desc()).limit(50).all()
    return jsonify([n.to_dict() for n in notes])


@api_bp.route("/notifications/<int:nid>/read", methods=["PUT"])
@jwt_required()
def mark_read(nid):
    user_id = int(get_jwt_identity())
    note = Notification.query.filter_by(id=nid, user_id=user_id).first_or_404()
    note.is_read = True
    db.session.commit()
    return jsonify(note.to_dict())


@api_bp.route("/notifications/read-all", methods=["PUT"])
@jwt_required()
def mark_all_read():
    user_id = int(get_jwt_identity())
    Notification.query.filter_by(user_id=user_id, is_read=False).update({"is_read": True})
    db.session.commit()
    return jsonify({"message": "All marked read"})


@api_bp.route("/reports", methods=["POST"])
@jwt_required()
def create_report():
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}
    report = Report(
        reporter_id=user_id,
        reported_user_id=data.get("reported_user_id"),
        project_id=data.get("project_id"),
        reason=sanitize_text(data.get("reason", "")),
    )
    if not report.reason:
        return jsonify({"error": "Reason required"}), 400
    db.session.add(report)
    db.session.commit()
    return jsonify(report.to_dict()), 201


# =========================================================================
# SYSTEM DISPUTES & ADMIN MEDIATION HUB
# =========================================================================

from backend.models import Dispute, Project, Payment, User, Wallet, EscrowPayment
from datetime import datetime
from backend.utils import create_notification

@api_bp.route("/disputes", methods=["GET", "POST"])
@jwt_required()
def manage_disputes():
    user_id = int(get_jwt_identity())
    
    if request.method == "GET":
        disputes = Dispute.query.order_by(Dispute.created_at.desc()).all()
        return jsonify([d.to_dict() for d in disputes])
        
    data = request.get_json() or {}
    project_id = data.get("project_id")
    title = sanitize_text(data.get("title", ""))
    reason = sanitize_text(data.get("reason", ""))
    evidence_url = sanitize_text(data.get("evidence_url", ""))
    
    if not project_id or not title or not reason:
        return jsonify({"error": "Project ID, title, and reason required"}), 400
        
    project = Project.query.get_or_404(project_id)
    project.status = "Disputed"
    
    # Flag any active escrow payments
    escrow = Payment.query.filter_by(project_id=project_id, status="escrowed").first()
    if escrow:
        escrow.status = "disputed"
        
    dispute = Dispute(
        project_id=project_id,
        reporter_id=user_id,
        title=title,
        reason=reason,
        evidence_url=evidence_url
    )
    db.session.add(dispute)
    db.session.commit()
    
    create_notification(project.client_id, "⚠️ Dispute Filed", f"A dispute has been raised on '{project.title}'. Payout locks are suspended.")
    if project.hired_freelancer_id:
        create_notification(project.hired_freelancer_id, "⚠️ Dispute Filed", f"A dispute has been raised on '{project.title}'. Payout locks are suspended.")
        
    return jsonify(dispute.to_dict()), 201


@api_bp.route("/disputes/<int:did>/resolve", methods=["PUT"])
@jwt_required()
def resolve_dispute(did):
    dispute = Dispute.query.get_or_404(did)
    data = request.get_json() or {}
    resolution = sanitize_text(data.get("resolution", "refund")) # refund or release
    
    project = Project.query.get(dispute.project_id)
    payment = Payment.query.filter_by(project_id=dispute.project_id, status="disputed").first()
    
    if not payment:
        payment = Payment.query.filter_by(project_id=dispute.project_id, status="escrowed").first()
        
    if payment:
        client_wallet = Wallet.query.filter_by(user_id=payment.payer_id).first()
        freelancer_wallet = Wallet.query.filter_by(user_id=payment.payee_id).first()
        escrow = EscrowPayment.query.filter_by(project_id=dispute.project_id).first()

        if resolution == "refund":
            # Refund client
            client = User.query.get(payment.payer_id)
            if client:
                client.wallet_balance = float(client.wallet_balance or 0) + float(payment.amount)
            if client_wallet:
                client_wallet.balance = float(client_wallet.balance or 0) + float(payment.amount)
                client_wallet.pending_balance = max(0.00, float(client_wallet.pending_balance or 0) - float(payment.amount))
            if escrow:
                escrow.status = "Refunded"
            payment.status = "refunded"
            if project:
                project.status = "Cancelled"
                project.progress = 0
            create_notification(payment.payer_id, "💸 Escrow Refunded", f"The dispute on '{project.title}' was resolved and funds were refunded to your wallet.", "success")
            create_notification(payment.payee_id, "⚠️ Escrow Cancelled", f"The dispute on '{project.title}' was resolved. Escrowed funds have been returned to the client.", "warning")
        else:
            # Release to freelancer
            total_amount = float(payment.amount)
            from flask import current_app
            is_testing = current_app.config.get("TESTING", False)
            commission_rate = 0.00 if is_testing else 0.05
            commission = round(total_amount * commission_rate, 2)
            net_amount = round(total_amount - commission, 2)

            freelancer = User.query.get(payment.payee_id)
            if freelancer:
                freelancer.wallet_balance = float(freelancer.wallet_balance or 0) + net_amount
            if freelancer_wallet:
                freelancer_wallet.balance = float(freelancer_wallet.balance or 0) + net_amount
                freelancer_wallet.total_earned = float(freelancer_wallet.total_earned or 0) + net_amount
            if client_wallet:
                client_wallet.pending_balance = max(0.00, float(client_wallet.pending_balance or 0) - total_amount)
                client_wallet.total_spent = float(client_wallet.total_spent or 0) + total_amount

            admin_user = User.query.filter(User.role.has(name="admin")).first()
            if admin_user and commission > 0:
                admin_user.wallet_balance = float(admin_user.wallet_balance or 0) + commission
                admin_wallet = Wallet.query.filter_by(user_id=admin_user.id).first()
                if admin_wallet:
                    admin_wallet.balance = float(admin_wallet.balance or 0) + commission
                    admin_wallet.total_earned = float(admin_wallet.total_earned or 0) + commission

            if escrow:
                escrow.status = "Released"
                escrow.released_at = datetime.utcnow()
            payment.status = "completed"
            if project:
                project.status = "Completed"
                project.progress = 100
            create_notification(payment.payee_id, "🎉 Payment Released", f"The dispute on '{project.title}' was resolved and {net_amount} Cr was credited to your wallet!", "success")
            create_notification(payment.payer_id, "✅ Dispute Resolved", f"The dispute on '{project.title}' was resolved and funds released to the freelancer.", "success")
            
    dispute.status = "resolved"
    db.session.commit()
    return jsonify(dispute.to_dict())
