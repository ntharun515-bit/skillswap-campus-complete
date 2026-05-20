"""Automated security penetration and boundary validation tests for SkillSwap."""
import os
import sys
import unittest
import json

# Append workspace path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from backend.extensions import db
from backend.models import User, Role, Wallet, Transaction
from flask_jwt_extended import create_access_token


class SkillSwapSecurityTests(unittest.TestCase):
    def setUp(self):
        """Setup isolated test SQLite context and seed data."""
        self.app = create_app("testing")
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        
        db.create_all()
        self._seed_data()

    def tearDown(self):
        """Clean database and pop context."""
        db.session.rollback()
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _seed_data(self):
        """Seed roles and user account."""
        # Roles
        self.client_role = Role.query.filter_by(name="client").first()
        if not self.client_role:
            self.client_role = Role(name="client")
            db.session.add(self.client_role)
            db.session.commit()

        # User
        self.user = User.query.filter_by(email="legitclient@campus.edu").first()
        if not self.user:
            self.user = User(
                email="legitclient@campus.edu",
                password_hash="Password123!",
                full_name="Legit Jordan",
                role_id=self.client_role.id
            )
            db.session.add(self.user)
            db.session.commit()

        # Initialize wallet
        self.wallet = Wallet.query.filter_by(user_id=self.user.id).first()
        if not self.wallet:
            self.wallet = Wallet(
                user_id=self.user.id,
                balance=1000.00,
                pending_balance=0.00,
                total_earned=0.00,
                total_spent=0.00
            )
            db.session.add(self.wallet)
            db.session.commit()

    def test_sql_injection_defense(self):
        """Test SQL Injection attacks on search fields and input payloads are cleanly blocked."""
        # 1. Attempt login SQL Injection bypass
        malicious_payload = {
            "email": "' OR '1'='1",
            "password": "' OR '1'='1"
        }
        res = self.client.post("/api/auth/login", json=malicious_payload)
        # Authentication should fail cleanly and return 401 Unauthorized, never executing as raw SQL
        self.assertEqual(res.status_code, 401)
        self.assertIn("Invalid email or password", res.json.get("error", ""))

        # 2. Attempt project search SQL Injection
        # Ripgrep search query with malicious payload
        res_search = self.client.get("/api/projects?q='; DROP TABLE projects; --")
        # Should execute successfully as a text query (returning 0 matches) instead of breaking tables
        self.assertEqual(res_search.status_code, 200)
        self.assertEqual(len(res_search.json), 0)

    def test_wallet_boundary_and_negative_amounts(self):
        """Test that negative budget allocations and excessive top-ups are blocked."""
        # Generate token
        token = create_access_token(identity=str(self.user.id))
        headers = {"Authorization": f"Bearer {token}"}

        # 1. Attempt deposit of negative virtual credits (-$500)
        res_neg = self.client.post(
            "/api/wallet/add-funds",
            json={"amount": -500.00},
            headers=headers
        )
        # Should return 400 Bad Request, keeping available wallet balance at $1000
        self.assertEqual(res_neg.status_code, 400)
        self.assertIn("error", res_neg.json)

        # Confirm balance remains unaffected
        db.session.refresh(self.wallet)
        self.assertEqual(self.wallet.balance, 1000.00)

        # 2. Attempt excessive deposit (+$999999) above limit
        res_limit = self.client.post(
            "/api/wallet/add-funds",
            json={"amount": 999999.00},
            headers=headers
        )
        # Should return 400 Bad Request
        self.assertEqual(res_limit.status_code, 400)

    def test_invalid_jwt_handling(self):
        """Test protected routes cleanly reject unauthorized or forged signature JWTs."""
        # 1. Attempt access with no token
        res_none = self.client.get("/api/wallet/balance")
        self.assertEqual(res_none.status_code, 401)

        # 2. Attempt access with invalid JWT signature
        res_bad = self.client.get(
            "/api/wallet/balance",
            headers={"Authorization": "Bearer bad_signature_token_payload"}
        )
        # Custom invalid token callback registered in app.py should return 401 and 'Invalid token'
        self.assertEqual(res_bad.status_code, 401)
        self.assertEqual(res_bad.json.get("error"), "Invalid token")


if __name__ == "__main__":
    unittest.main()
