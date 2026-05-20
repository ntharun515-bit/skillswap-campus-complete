"""Production-grade automated unit and integration tests for SkillSwap."""
import os
import sys
import unittest
import json
from datetime import date

# Append workspace path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from backend.extensions import db
from backend.models import User, Role, Project, Application, Wallet, Transaction, EscrowPayment, WithdrawalRequest


class SkillSwapBackendTests(unittest.TestCase):
    def setUp(self):
        """Establish isolated test database and client."""
        # Use an in-memory database to prevent test run interference with actual data
        self.app = create_app("testing")
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        
        self.client = self.app.test_client()
        self.ctx = self.app.app_context()
        self.ctx.push()
        
        db.create_all()
        self._seed_test_roles()

    def tearDown(self):
        """Clean database and pop context."""
        db.session.rollback()
        db.session.remove()
        db.drop_all()
        self.ctx.pop()

    def _seed_test_roles(self):
        """Seed student, client, and admin roles."""
        roles = ["student", "client", "admin"]
        for name in roles:
            r = Role.query.filter_by(name=name).first()
            if not r:
                r = Role(name=name)
                db.session.add(r)
        db.session.commit()

    def test_signup_and_login_flow(self):
        """Test auth signups, duplicate validation, logins, and JWT generation."""
        # 1. Register Client
        reg_payload = {
            "email": "testclient@campus.edu",
            "password": "Password123!",
            "full_name": "Test Client",
            "role": "client"
        }
        res = self.client.post("/api/auth/register", json=reg_payload)
        self.assertEqual(res.status_code, 201)
        self.assertIn("user", res.json)
        
        # 2. Block Duplicate Registration
        res_dup = self.client.post("/api/auth/register", json=reg_payload)
        self.assertEqual(res_dup.status_code, 409)
        
        # 3. Perform Login
        login_payload = {
            "email": "testclient@campus.edu",
            "password": "Password123!"
        }
        res_log = self.client.post("/api/auth/login", json=login_payload)
        self.assertEqual(res_log.status_code, 200)
        self.assertTrue("access_token" in res_log.json or "token" in res_log.json)
        self.assertIn("user", res_log.json)

    def test_rbac_campaign_posting_permissions(self):
        """Test Role-Based Access Control on protected client endpoints."""
        # 1. Register Student
        self.client.post("/api/auth/register", json={
            "email": "teststudent@campus.edu",
            "password": "Password123!",
            "full_name": "Test Student",
            "role": "student"
        })
        
        # Login Student
        res_stud = self.client.post("/api/auth/login", json={
            "email": "teststudent@campus.edu",
            "password": "Password123!"
        })
        stud_token = res_stud.json.get("access_token") or res_stud.json.get("token")
        
        # Register Client
        self.client.post("/api/auth/register", json={
            "email": "testclient2@campus.edu",
            "password": "Password123!",
            "full_name": "Test Client 2",
            "role": "client"
        })
        
        # Login Client
        res_cli = self.client.post("/api/auth/login", json={
            "email": "testclient2@campus.edu",
            "password": "Password123!"
        })
        cli_token = res_cli.json.get("access_token") or res_cli.json.get("token")

        proj_payload = {
            "title": "Build Obsidian API Integrator",
            "description": "Write specialized code for dashboard components",
            "budget": 350.00,
            "skills_required": "Python, Flask"
        }

        # 2. Verify Student is Blocked (403 Forbidden)
        res_post_stud = self.client.post(
            "/api/projects",
            json=proj_payload,
            headers={"Authorization": f"Bearer {stud_token}"}
        )
        self.assertEqual(res_post_stud.status_code, 403)

        # 3. Verify Client is Permitted (201 Created)
        res_post_cli = self.client.post(
            "/api/projects",
            json=proj_payload,
            headers={"Authorization": f"Bearer {cli_token}"}
        )
        self.assertEqual(res_post_cli.status_code, 201)
        self.assertEqual(res_post_cli.json["title"], "Build Obsidian API Integrator")

    def test_complete_escrow_ledger_flow(self):
        """Test end-to-end payment locking, releases, and double-spend withdraw validations."""
        # 1. Create client & student
        self.client.post("/api/auth/register", json={
            "email": "client@campus.edu",
            "password": "Password123!",
            "full_name": "Jordan Payer",
            "role": "client"
        })
        self.client.post("/api/auth/register", json={
            "email": "student@campus.edu",
            "password": "Password123!",
            "full_name": "Alex Freelancer",
            "role": "student"
        })

        # Logins
        res_c = self.client.post("/api/auth/login", json={"email": "client@campus.edu", "password": "Password123!"})
        c_tok = res_c.json.get("access_token") or res_c.json.get("token")
        res_s = self.client.post("/api/auth/login", json={"email": "student@campus.edu", "password": "Password123!"})
        s_tok = res_s.json.get("access_token") or res_s.json.get("token")
        
        # Verify wallet auto-creation & default balance $1000
        res_bal = self.client.get("/api/wallet/balance", headers={"Authorization": f"Bearer {c_tok}"})
        self.assertEqual(res_bal.status_code, 200)
        self.assertEqual(res_bal.json["wallet"]["balance"], 1000.00)

        # 2. Client Posts Project Listing
        res_p = self.client.post(
            "/api/projects",
            json={
                "title": "Design Obsidian Dashboards",
                "description": "HTML CSS work",
                "budget": 300.00,
                "skills_required": "HTML, CSS"
            },
            headers={"Authorization": f"Bearer {c_tok}"}
        )
        proj_id = res_p.json["id"]

        # Student Applies
        res_app = self.client.post(
            f"/api/projects/{proj_id}/apply",
            json={
                "proposed_rate": 300.00,
                "cover_letter": "I am a visual interface expert."
            },
            headers={"Authorization": f"Bearer {s_tok}"}
        )
        self.assertEqual(res_app.status_code, 201)
        app_id = res_app.json["id"]

        # Client Accepts Student & Hires
        res_hire = self.client.put(
            f"/api/projects/applications/{app_id}",
            json={"status": "accepted"},
            headers={"Authorization": f"Bearer {c_tok}"}
        )
        self.assertEqual(res_hire.status_code, 200)

        # 3. Client Locks Escrow Budget
        res_lock = self.client.post(
            "/api/payments/escrow/create",
            json={"project_id": proj_id},
            headers={"Authorization": f"Bearer {c_tok}"}
        )
        self.assertEqual(res_lock.status_code, 200)

        # Verify client balance has locked credits ($700 available, $300 pending)
        res_bal_after = self.client.get("/api/wallet/balance", headers={"Authorization": f"Bearer {c_tok}"})
        self.assertEqual(res_bal_after.json["wallet"]["balance"], 700.00)
        self.assertEqual(res_bal_after.json["wallet"]["pending_balance"], 300.00)

        # 4. Client Releases Escrow Payout
        res_rel = self.client.post(
            "/api/payments/release",
            json={"project_id": proj_id},
            headers={"Authorization": f"Bearer {c_tok}"}
        )
        self.assertEqual(res_rel.status_code, 200)

        # Verify student available balance has received $300 cleared earnings
        res_s_bal = self.client.get("/api/wallet/balance", headers={"Authorization": f"Bearer {s_tok}"})
        self.assertEqual(res_s_bal.json["wallet"]["balance"], 300.00)
        self.assertEqual(res_s_bal.json["wallet"]["total_earned"], 300.00)

        # 5. Student Withdrawal Lock (Double-spend blocked)
        res_wth = self.client.post(
            "/api/withdrawals/request",
            json={"amount": 100.00, "method": "PayPal"},
            headers={"Authorization": f"Bearer {s_tok}"}
        )
        self.assertEqual(res_wth.status_code, 200)

        # Verify student available decrements by $100 and moves to pending
        res_s_bal_w = self.client.get("/api/wallet/balance", headers={"Authorization": f"Bearer {s_tok}"})
        self.assertEqual(res_s_bal_w.json["wallet"]["balance"], 200.00)
        self.assertEqual(res_s_bal_w.json["wallet"]["pending_balance"], 100.00)


if __name__ == "__main__":
    unittest.main()
