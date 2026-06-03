import os
from backend.app import app
from backend.extensions import db
from backend.models import Dispute, EscrowPayment, Payment, Project, Wallet

def force_resolve_all_disputes():
    with app.app_context():
        disputes = Dispute.query.filter_by(status='open').all()
        if not disputes:
            print("No open disputes found.")
            return

        for d in disputes:
            print(f"Resolving Dispute ID: {d.id} for Project ID: {d.project_id}")
            
            project = Project.query.get(d.project_id)
            if project:
                project.status = "Completed"
                
            # Legacy payment resolution
            legacy_payment = Payment.query.filter_by(project_id=d.project_id).first()
            if legacy_payment:
                legacy_payment.status = "released"
                
            # Escrow payment resolution
            escrow = EscrowPayment.query.filter_by(project_id=d.project_id).first()
            if escrow:
                escrow.status = "released"
                # Forcing funds to freelancer wallet as resolution
                freelancer_wallet = Wallet.query.filter_by(user_id=escrow.freelancer_id).first()
                if freelancer_wallet:
                    freelancer_wallet.balance = float(freelancer_wallet.balance) + escrow.amount
                    freelancer_wallet.total_earned = float(freelancer_wallet.total_earned) + escrow.amount

            d.status = "resolved"
        
        db.session.commit()
        print(f"Successfully resolved {len(disputes)} open disputes and released funds.")

if __name__ == "__main__":
    force_resolve_all_disputes()
