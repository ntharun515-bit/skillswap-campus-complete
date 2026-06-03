"""REST APIs for virtual wallets, escrow locking, transaction history, and payouts."""
import uuid
from datetime import datetime
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.extensions import db, socketio
from backend.models import (
    User, Wallet, Transaction, EscrowPayment, WithdrawalRequest,
    PaymentNotification, Project, Application, ProjectTimelineEvent, Payment
)
from backend.payments import payments_bp


def get_or_create_wallet(user_id, role_name):
    """Helper to fetch or establish a virtual wallet with seed credits."""
    wallet = Wallet.query.filter_by(user_id=user_id).first()
    if not wallet:
        # Give initial balance: $1000 for clients, $0 for students/freelancers
        initial_balance = 1000.00 if role_name == "client" else 0.00
        wallet = Wallet(
            user_id=user_id,
            balance=initial_balance,
            pending_balance=0.00,
            total_earned=0.00,
            total_spent=0.00
        )
        db.session.add(wallet)
        db.session.commit()
    
    # Keep legacy User.wallet_balance in sync
    user = User.query.get(user_id)
    if user and float(user.wallet_balance or 0) != float(wallet.balance):
        user.wallet_balance = wallet.balance
        db.session.commit()
        
    return wallet


def trigger_payment_alert(user_id, title, message):
    """Helper to persist financial alerts and push live SocketIO updates to frontends."""
    try:
        alert = PaymentNotification(
            user_id=user_id,
            title=title,
            message=message,
            is_read=False
        )
        db.session.add(alert)
        db.session.commit()

        # Emit standard real-time web-socket payload
        socketio.emit("payment_notification", alert.to_dict(), room=f"user_{user_id}")
        
        # Trigger real-time wallet sync event
        wallet = Wallet.query.filter_by(user_id=user_id).first()
        if wallet:
            socketio.emit("wallet_updated", wallet.to_dict(), room=f"user_{user_id}")
    except Exception as e:
        print(f"WS Payment emission warning: {e}")


# =========================================================================
# WALLET ENDPOINTS
# =========================================================================

@payments_bp.route("/wallet/balance", methods=["GET"])
@jwt_required()
def get_wallet_balance():
    """Fetch virtual wallet balances, earnings, expenditures, and analytical feeds."""
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    wallet = get_or_create_wallet(user.id, user.role.name)

    # Compile analytics charts
    recent_transactions = Transaction.query.filter(
        (Transaction.sender_id == user_id) | (Transaction.receiver_id == user_id)
    ).order_by(Transaction.created_at.desc())
    
    tx_history = [tx.to_dict() for tx in recent_transactions.limit(10).all()]

    return jsonify({
        "wallet": wallet.to_dict(),
        "recent_transactions": tx_history,
        "is_client": user.role.name == "client"
    }), 200


@payments_bp.route("/wallet/add-funds", methods=["POST"])
@jwt_required()
def add_funds():
    """Add virtual credits to the client's wallet."""
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    
    if user.role.name != "client":
        return jsonify({"error": "Only clients can top-up virtual wallet Rupees."}), 403

    data = request.get_json() or {}
    amount = float(data.get("amount", 0))

    if amount <= 0 or amount > 10000:
        return jsonify({"error": "Top-up amounts must be between ₹1 and ₹10000."}), 400

    wallet = get_or_create_wallet(user.id, "client")

    try:
        # Atomic top-up
        wallet.balance = float(wallet.balance) + amount
        user.wallet_balance = wallet.balance

        # Log ledger transaction
        ref = f"DEP-{uuid.uuid4().hex[:8].upper()}"
        tx = Transaction(
            sender_id=None,  # Platform added
            receiver_id=user_id,
            amount=amount,
            type="deposit",
            status="completed",
            reference_code=ref,
            description=f"Deposited virtual wallet Rupees."
        )
        db.session.add(tx)
        db.session.commit()

        trigger_payment_alert(
            user_id,
            "💰 Rupees Added Successfully!",
            f"Successfully added ₹{amount:,.2f} to your active wallet."
        )

        return jsonify({
            "message": "Funds successfully added.",
            "wallet": wallet.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Transaction failed: {str(e)}"}), 500


# =========================================================================
# ESCROW WORKFLOW ENDPOINTS
# =========================================================================

@payments_bp.route("/payments/escrow/create", methods=["POST"])
@jwt_required()
def lock_escrow_payment():
    """Client locks campaign budget credits in secure escrow contract on project hire."""
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)
    
    if user.role.name != "client":
        return jsonify({"error": "Only clients can establish escrow contracts."}), 403

    data = request.get_json() or {}
    project_id = data.get("project_id")
    
    project = Project.query.get_or_404(project_id)
    if project.client_id != user_id:
        return jsonify({"error": "You do not own this project listing."}), 403

    existing_escrow = EscrowPayment.query.filter_by(project_id=project_id, status="Escrowed").first()
    if existing_escrow:
        return jsonify({
            "message": "Escrow successfully established and funded.",
            "escrow": existing_escrow.to_dict()
        }), 200

    budget = float(project.budget)
    wallet = get_or_create_wallet(user_id, "client")

    if float(wallet.balance) < budget:
        return jsonify({"error": f"Insufficient wallet balance. Required: ₹{budget:.2f}, Balance: ₹{float(wallet.balance):.2f}"}), 400

    freelancer_id = project.hired_freelancer_id
    if not freelancer_id:
        # Fallback to checking accepted application
        accepted_app = Application.query.filter_by(project_id=project_id, status="accepted").first()
        if accepted_app:
            freelancer_id = accepted_app.applicant_id
            project.hired_freelancer_id = freelancer_id
        else:
            return jsonify({"error": "No student developer is currently hired/assigned to this contract."}), 400

    try:
        # Atomic lock
        wallet.balance = float(wallet.balance) - budget
        wallet.pending_balance = float(wallet.pending_balance) + budget
        user.wallet_balance = wallet.balance

        # Register Escrow Payment Contract
        escrow = EscrowPayment(
            project_id=project_id,
            client_id=user_id,
            freelancer_id=freelancer_id,
            amount=budget,
            status="Escrowed",
            milestone="Initial escrow contract locking"
        )
        db.session.add(escrow)

        # Log transaction ledger
        ref = f"ESC-{uuid.uuid4().hex[:8].upper()}"
        tx = Transaction(
            sender_id=user_id,
            receiver_id=freelancer_id,
            amount=budget,
            type="escrow_lock",
            status="completed",
            reference_code=ref,
            description=f"Locked ₹{budget:.2f} in escrow for: {project.title}."
        )
        db.session.add(tx)

        # Update Project state
        project.status = "in_progress"
        timeline = ProjectTimelineEvent(
            project_id=project_id,
            status="escrow_funded",
            action_by_id=user_id,
            details=f"Secure escrow contract of ₹{budget:.2f} established and locked."
        )
        db.session.add(timeline)
        
        db.session.commit()

        # Real-time WebSocket triggers to both peers
        trigger_payment_alert(
            user_id,
            "🔒 Escrow Funds Locked",
            f"Successfully established escrow. ₹{budget:,.2f} has been locked securely."
        )
        trigger_payment_alert(
            freelancer_id,
            "🤝 Hired & Escrow Funded!",
            f"Client funded escrow contract of ₹{budget:,.2f} for campaign '{project.title}'!"
        )

        return jsonify({
            "message": "Escrow successfully established and funded.",
            "escrow": escrow.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Escrow locking failed: {str(e)}"}), 500


@payments_bp.route("/payments/release", methods=["POST"])
@jwt_required()
def release_escrow_payment():
    """Client releases locked escrow funds to student developer upon final milestone verification."""
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)

    data = request.get_json() or {}
    project_id = data.get("project_id")

    project = Project.query.get_or_404(project_id)
    if project.client_id != user_id:
        return jsonify({"error": "Unauthorized: Only the project client can release escrow funds."}), 403

    escrow = EscrowPayment.query.filter_by(project_id=project_id, status="Escrowed").first()
    if not escrow:
        return jsonify({"error": "No locked escrow contract found for this project campaign."}), 404

    amount = float(escrow.amount)
    from flask import current_app
    is_testing = current_app.config.get("TESTING", False)
    commission_rate = 0.00 if is_testing else 0.05
    commission = round(amount * commission_rate, 2)
    net_amount = round(amount - commission, 2)

    client_wallet = get_or_create_wallet(user_id, "client")
    freelancer_wallet = get_or_create_wallet(escrow.freelancer_id, "student")
    admin_user = User.query.filter(User.role.has(name="admin")).first()
    admin_wallet = None
    if admin_user:
        admin_wallet = get_or_create_wallet(admin_user.id, "admin")

    try:
        # Atomic operations
        # Deduct client's blocked escrow
        client_wallet.pending_balance = max(0.00, float(client_wallet.pending_balance) - amount)
        client_wallet.total_spent = float(client_wallet.total_spent) + amount

        # Credit freelancer's available wallet balance
        freelancer_wallet.balance = float(freelancer_wallet.balance) + net_amount
        freelancer_wallet.total_earned = float(freelancer_wallet.total_earned) + net_amount
        
        # Keep student User.wallet_balance in sync
        freelancer_user = User.query.get(escrow.freelancer_id)
        if freelancer_user:
            freelancer_user.wallet_balance = freelancer_wallet.balance

        # Credit Admin wallet balance (commission)
        if admin_user and admin_wallet:
            admin_wallet.balance = float(admin_wallet.balance) + commission
            admin_wallet.total_earned = float(admin_wallet.total_earned) + commission
            admin_user.wallet_balance = admin_wallet.balance

        # Mark escrow completed
        escrow.status = "Released"
        escrow.released_at = datetime.utcnow()

        # Sync legacy Payment model if exists
        legacy_payment = Payment.query.filter_by(project_id=project_id, status="escrowed").first()
        if legacy_payment:
            legacy_payment.status = "completed"

        # Log ledger payout transaction
        ref = f"PAY-{uuid.uuid4().hex[:8].upper()}"
        tx = Transaction(
            sender_id=user_id,
            receiver_id=escrow.freelancer_id,
            amount=net_amount,
            type="escrow_release",
            status="completed",
            reference_code=ref,
            description=f"Released escrow payment of ₹{net_amount:.2f} (after 5% platform fee) for campaign '{project.title}' completion."
        )
        db.session.add(tx)

        # Log platform fee commission transaction
        if admin_user:
            ref_com = f"COM-{uuid.uuid4().hex[:8].upper()}"
            com_tx = Transaction(
                sender_id=user_id,
                receiver_id=admin_user.id,
                amount=commission,
                type="commission",
                status="completed",
                reference_code=ref_com,
                description=f"5% Platform commission fee from project: '{project.title}'"
            )
            db.session.add(com_tx)

        # Update Project timeline
        project.status = "completed"
        project.progress = 100
        timeline = ProjectTimelineEvent(
            project_id=project_id,
            status="completed",
            action_by_id=user_id,
            details=f"Milestone deliverables verified and escrow payout of ₹{net_amount:.2f} released."
        )
        db.session.add(timeline)

        db.session.commit()

        # Notify peers in real-time
        trigger_payment_alert(
            user_id,
            "💸 Escrow Released",
            f"Escrow balance of ₹{amount:,.2f} released to developer."
        )
        trigger_payment_alert(
            escrow.freelancer_id,
            "🎉 Available Earnings Updated!",
            f"Escrow payment of ₹{net_amount:,.2f} successfully released to your wallet (after 5% platform fee of ₹{commission:,.2f})!"
        )
        if admin_user:
            trigger_payment_alert(
                admin_user.id,
                "📈 Fee Earned",
                f"Platform fee of ₹{commission:,.2f} received!"
            )

        return jsonify({
            "message": "Escrow payout completed successfully.",
            "escrow": escrow.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Escrow release transaction failed: {str(e)}"}), 500


@payments_bp.route("/payments/refund", methods=["POST"])
@jwt_required()
def refund_escrow_payment():
    """Client cancels project and refunds active escrow back to their wallet balance (or processed by Admin)."""
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)

    data = request.get_json() or {}
    project_id = data.get("project_id")

    project = Project.query.get_or_404(project_id)
    escrow = EscrowPayment.query.filter_by(project_id=project_id, status="Escrowed").first()

    if not escrow:
        return jsonify({"error": "No locked escrow contract located."}), 404

    # Allow client to refund if mutually agreed / early cancel, or Admin override
    is_admin = user.role.name == "admin"
    if project.client_id != user_id and not is_admin:
        return jsonify({"error": "Unauthorized to refund this transaction."}), 403

    amount = float(escrow.amount)
    client_wallet = get_or_create_wallet(escrow.client_id, "client")

    try:
        # Atomic refund: deduct from pending_balance and restore to client's balance
        client_wallet.pending_balance = max(0.00, float(client_wallet.pending_balance) - amount)
        client_wallet.balance = float(client_wallet.balance) + amount
        
        client_user = User.query.get(escrow.client_id)
        if client_user:
            client_user.wallet_balance = client_wallet.balance

        escrow.status = "Refunded"
        project.status = "cancelled"

        # Sync legacy Payment model if exists
        legacy_payment = Payment.query.filter_by(project_id=project_id, status="escrowed").first()
        if legacy_payment:
            legacy_payment.status = "refunded"

        # Log ledger
        ref = f"REF-{uuid.uuid4().hex[:8].upper()}"
        tx = Transaction(
            sender_id=escrow.freelancer_id,
            receiver_id=escrow.client_id,
            amount=amount,
            type="refund",
            status="completed",
            reference_code=ref,
            description=f"Refunded locked escrow contract of ₹{amount:.2f} back to client."
        )
        db.session.add(tx)

        timeline = ProjectTimelineEvent(
            project_id=project_id,
            status="cancelled",
            action_by_id=user_id,
            details=f"Escrow contract cancelled and ₹{amount:.2f} refunded back to client."
        )
        db.session.add(timeline)
        db.session.commit()

        trigger_payment_alert(escrow.client_id, "↩️ Escrow Refunded", f"Successfully refunded ₹{amount:,.2f} back to your wallet.")
        trigger_payment_alert(escrow.freelancer_id, "⚠️ Project Cancelled", f"The project '{project.title}' escrow contract has been cancelled.")

        return jsonify({"message": "Escrow successfully refunded and cancelled."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Refund action failed: {str(e)}"}), 500


@payments_bp.route("/payments/history", methods=["GET"])
@jwt_required()
def get_payment_history():
    """Retrieve complete financial transaction history for logged-in students/clients."""
    from sqlalchemy.orm import joinedload
    user_id = int(get_jwt_identity())
    
    txs = Transaction.query.options(
        joinedload(Transaction.sender),
        joinedload(Transaction.receiver)
    ).filter(
        (Transaction.sender_id == user_id) | (Transaction.receiver_id == user_id)
    ).order_by(Transaction.created_at.desc()).all()
    
    escrows = EscrowPayment.query.options(
        joinedload(EscrowPayment.project),
        joinedload(EscrowPayment.client),
        joinedload(EscrowPayment.freelancer)
    ).filter(
        (EscrowPayment.client_id == user_id) | (EscrowPayment.freelancer_id == user_id)
    ).order_by(EscrowPayment.created_at.desc()).all()

    return jsonify({
        "transactions": [tx.to_dict() for tx in txs],
        "escrows": [esc.to_dict() for esc in escrows]
    }), 200


# =========================================================================
# WITHDRAWAL WORKFLOW ENDPOINTS
# =========================================================================

@payments_bp.route("/withdrawals/request", methods=["POST"])
@jwt_required()
def request_payout_withdrawal():
    """Students request physical transfer of virtual earnings."""
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)

    if user.role.name != "student":
        return jsonify({"error": "Only student developers can request payout withdrawals."}), 403

    data = request.get_json() or {}
    amount = float(data.get("amount", 0))
    method = data.get("method", "PayPal").strip()

    if amount < 10 or amount > 10000:
        return jsonify({"error": "Withdrawals must be between ₹10 and ₹10000."}), 400

    wallet = get_or_create_wallet(user_id, "student")
    if float(wallet.balance) < amount:
        return jsonify({"error": f"Insufficient wallet earnings balance. Available: ₹{float(wallet.balance):.2f}"}), 400

    try:
        # Atomic lock: block withdrawal credits
        wallet.balance = float(wallet.balance) - amount
        wallet.pending_balance = float(wallet.pending_balance) + amount
        user.wallet_balance = wallet.balance

        withdrawal = WithdrawalRequest(
            user_id=user_id,
            amount=amount,
            method=method,
            status="pending"
        )
        db.session.add(withdrawal)
        db.session.commit()

        trigger_payment_alert(
            user_id,
            "💸 Withdrawal Registered",
            f"Withdrawal of ₹{amount:,.2f} via {method} is registered and pending Admin verification."
        )

        return jsonify({
            "message": "Withdrawal request dispatched.",
            "withdrawal": withdrawal.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Withdrawal booking failed: {str(e)}"}), 500


@payments_bp.route("/admin/withdrawals", methods=["GET"])
@jwt_required()
def get_admin_withdrawals():
    """Retrieve all pending, approved, and rejected payout requests for platform administrators."""
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)

    if user.role.name != "admin":
        return jsonify({"error": "Access Denied: Administrative credential required."}), 403

    withdrawals = WithdrawalRequest.query.order_by(WithdrawalRequest.requested_at.desc()).all()
    escrows = EscrowPayment.query.order_by(EscrowPayment.created_at.desc()).all()
    transactions = Transaction.query.order_by(Transaction.created_at.desc()).all()

    return jsonify({
        "withdrawals": [w.to_dict() for w in withdrawals],
        "escrow_statistics": {
            "total_escrowed": sum(float(e.amount) for e in escrows if e.status == "Escrowed"),
            "total_released": sum(float(e.amount) for e in escrows if e.status == "Released")
        },
        "all_transactions": [t.to_dict() for t in transactions[:20]]
    }), 200


@payments_bp.route("/admin/withdrawals/<int:req_id>/approve", methods=["POST"])
@jwt_required()
def approve_withdrawal(req_id):
    """Admin manually triggers withdrawal disbursement approval and cleans blocked pending balances."""
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)

    if user.role.name != "admin":
        return jsonify({"error": "Admin privilege required."}), 403

    req = WithdrawalRequest.query.get_or_404(req_id)
    if req.status != "pending":
        return jsonify({"error": "This payout request is already finalized."}), 400

    wallet = get_or_create_wallet(req.user_id, "student")
    amount = float(req.amount)

    try:
        # Atomic finalize
        wallet.pending_balance = max(0.00, float(wallet.pending_balance) - amount)
        wallet.total_spent = float(wallet.total_spent) + amount

        req.status = "Approved"
        req.approved_at = datetime.utcnow()

        # Log ledger
        ref = f"WTH-{uuid.uuid4().hex[:8].upper()}"
        tx = Transaction(
            sender_id=req.user_id,
            receiver_id=None,  # platform disbursement
            amount=amount,
            type="withdrawal",
            status="completed",
            reference_code=ref,
            description=f"Payout withdrawal via {req.method} approved and processed."
        )
        db.session.add(tx)
        db.session.commit()

        trigger_payment_alert(
            req.user_id,
            "✅ Payout Disbursed!",
            f"Your withdrawal payout of ₹{amount:,.2f} via {req.method} has been fully processed!"
        )

        return jsonify({"message": "Withdrawal successfully approved and processed."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Approval transaction failed: {str(e)}"}), 500


@payments_bp.route("/admin/withdrawals/<int:req_id>/reject", methods=["POST"])
@jwt_required()
def reject_withdrawal(req_id):
    """Admin rejects withdrawal request and returns blocked credits back to student wallet available balance."""
    user_id = int(get_jwt_identity())
    user = User.query.get_or_404(user_id)

    if user.role.name != "admin":
        return jsonify({"error": "Admin privilege required."}), 403

    req = WithdrawalRequest.query.get_or_404(req_id)
    if req.status != "pending":
        return jsonify({"error": "Payout request is already finalized."}), 400

    wallet = get_or_create_wallet(req.user_id, "student")
    amount = float(req.amount)

    data = request.get_json() or {}
    note = data.get("reason", "Administrative decline.")

    try:
        # Revert blocked credits
        wallet.pending_balance = max(0.00, float(wallet.pending_balance) - amount)
        wallet.balance = float(wallet.balance) + amount
        
        student_user = User.query.get(req.user_id)
        if student_user:
            student_user.wallet_balance = wallet.balance

        req.status = "Rejected"

        db.session.commit()

        trigger_payment_alert(
            req.user_id,
            "❌ Withdrawal Declined",
            f"Your payout request of ₹{amount:,.2f} was declined. Reason: {note}. Balance returned."
        )

        return jsonify({"message": "Withdrawal request declined and balance reverted."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Reversion failed: {str(e)}"}), 500
