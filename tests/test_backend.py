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

    def test_applicant_capability_indicators(self):
        """Verify applicant API responses include student capability fields for client hiring decisions."""
        # Setup client
        self.client.post("/api/auth/register", json={
            "email": "cap_client@campus.edu", "password": "Password123!",
            "full_name": "Cap Client", "role": "client"
        })
        self.client.post("/api/auth/register", json={
            "email": "cap_student@campus.edu", "password": "Password123!",
            "full_name": "Cap Student", "role": "student"
        })
        c_res = self.client.post("/api/auth/login", json={"email": "cap_client@campus.edu", "password": "Password123!"})
        c_tok = c_res.json.get("access_token") or c_res.json.get("token")
        s_res = self.client.post("/api/auth/login", json={"email": "cap_student@campus.edu", "password": "Password123!"})
        s_tok = s_res.json.get("access_token") or s_res.json.get("token")

        # Client posts project
        p_res = self.client.post("/api/projects", json={
            "title": "Capability Test Project", "description": "Testing capability fields",
            "budget": 250.00, "skills_required": "Python"
        }, headers={"Authorization": f"Bearer {c_tok}"})
        proj_id = p_res.json["id"]

        # Student applies
        app_res = self.client.post(f"/api/projects/{proj_id}/apply", json={
            "proposed_rate": 250.00,
            "cover_letter": "I am highly skilled in Python development."
        }, headers={"Authorization": f"Bearer {s_tok}"})
        self.assertEqual(app_res.status_code, 201)

        # Client retrieves applications
        apps_res = self.client.get(f"/api/projects/{proj_id}/applications",
                                   headers={"Authorization": f"Bearer {c_tok}"})
        self.assertEqual(apps_res.status_code, 200)
        apps = apps_res.json
        self.assertEqual(len(apps), 1)

        a = apps[0]
        # Assert all capability indicator fields are present in the response
        self.assertIn("applicant_headline", a)
        self.assertIn("applicant_level", a)
        self.assertIn("applicant_rating_avg", a)
        self.assertIn("applicant_rating_count", a)
        self.assertIn("applicant_slug", a)

        # By default for a new student: level=Rookie, avg=0.0, count=0, slug=None
        self.assertEqual(a["applicant_level"], "Rookie")
        self.assertEqual(a["applicant_rating_avg"], 0.0)
        self.assertEqual(a["applicant_rating_count"], 0)
        self.assertIsNone(a["applicant_slug"])

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

    def test_client_review_system_integration(self):
        """Test review creation, rating limits, security controls, profile updates, and idempotency."""
        # 1. Create client & students
        self.client.post("/api/auth/register", json={
            "email": "review_client@campus.edu",
            "password": "Password123!",
            "full_name": "Review Client",
            "role": "client"
        })
        self.client.post("/api/auth/register", json={
            "email": "review_student@campus.edu",
            "password": "Password123!",
            "full_name": "Review Freelancer",
            "role": "student"
        })
        self.client.post("/api/auth/register", json={
            "email": "other_student@campus.edu",
            "password": "Password123!",
            "full_name": "Other Freelancer",
            "role": "student"
        })
        self.client.post("/api/auth/register", json={
            "email": "other_client@campus.edu",
            "password": "Password123!",
            "full_name": "Other Client",
            "role": "client"
        })

        # Logins
        c_res = self.client.post("/api/auth/login", json={"email": "review_client@campus.edu", "password": "Password123!"})
        c_tok = c_res.json.get("access_token") or c_res.json.get("token")
        
        s_res = self.client.post("/api/auth/login", json={"email": "review_student@campus.edu", "password": "Password123!"})
        s_tok = s_res.json.get("access_token") or s_res.json.get("token")
        s_user_id = s_res.json["user"]["id"]

        other_s_res = self.client.post("/api/auth/login", json={"email": "other_student@campus.edu", "password": "Password123!"})
        other_s_user_id = other_s_res.json["user"]["id"]

        other_c_res = self.client.post("/api/auth/login", json={"email": "other_client@campus.edu", "password": "Password123!"})
        other_c_tok = other_c_res.json.get("access_token") or other_c_res.json.get("token")

        # 2. Client Posts Project
        p_res = self.client.post(
            "/api/projects",
            json={
                "title": "Review Testing Campaign",
                "description": "Verification of review workflow",
                "budget": 200.00,
                "skills_required": "Flask"
            },
            headers={"Authorization": f"Bearer {c_tok}"}
        )
        proj_id = p_res.json["id"]

        # Student Applies
        app_res = self.client.post(
            f"/api/projects/{proj_id}/apply",
            json={
                "proposed_rate": 200.00,
                "cover_letter": "I will deliver excellent outcomes."
            },
            headers={"Authorization": f"Bearer {s_tok}"}
        )
        app_id = app_res.json["id"]

        # Client Accepts & Hires
        self.client.put(
            f"/api/projects/applications/{app_id}",
            json={"status": "accepted"},
            headers={"Authorization": f"Bearer {c_tok}"}
        )

        # 3. Test Invalid Rating Boundaries
        res_err_rating = self.client.post(
            f"/api/projects/{proj_id}/reviews",
            json={"reviewee_id": s_user_id, "rating": 6, "comment": "Amazing!"},
            headers={"Authorization": f"Bearer {c_tok}"}
        )
        self.assertEqual(res_err_rating.status_code, 400)

        res_err_rating2 = self.client.post(
            f"/api/projects/{proj_id}/reviews",
            json={"reviewee_id": s_user_id, "rating": 0, "comment": "Poor"},
            headers={"Authorization": f"Bearer {c_tok}"}
        )
        self.assertEqual(res_err_rating2.status_code, 400)

        # 4. Test Reviewing Non-Hired Freelancer
        res_err_unhired = self.client.post(
            f"/api/projects/{proj_id}/reviews",
            json={"reviewee_id": other_s_user_id, "rating": 5, "comment": "Good job"},
            headers={"Authorization": f"Bearer {c_tok}"}
        )
        self.assertEqual(res_err_unhired.status_code, 400)

        # 5. Test Unauthorized Client Review (from other_client)
        res_err_auth = self.client.post(
            f"/api/projects/{proj_id}/reviews",
            json={"reviewee_id": s_user_id, "rating": 5, "comment": "Trying to bypass"},
            headers={"Authorization": f"Bearer {other_c_tok}"}
        )
        self.assertEqual(res_err_auth.status_code, 403)

        # 6. Post valid review
        res_valid = self.client.post(
            f"/api/projects/{proj_id}/reviews",
            json={"reviewee_id": s_user_id, "rating": 5, "comment": "Stunning quality work!"},
            headers={"Authorization": f"Bearer {c_tok}"}
        )
        self.assertEqual(res_valid.status_code, 201)
        self.assertEqual(res_valid.json["rating"], 5)
        self.assertEqual(res_valid.json["comment"], "Stunning quality work!")

        # Verify rating updates on FreelancerProfile
        from backend.models import FreelancerProfile
        prof = FreelancerProfile.query.filter_by(user_id=s_user_id).first()
        self.assertIsNotNone(prof)
        self.assertEqual(prof.rating_count, 1)
        self.assertEqual(prof.rating_avg, 5.0)

        # 7. Test Idempotency (Updating the same review)
        res_update = self.client.post(
            f"/api/projects/{proj_id}/reviews",
            json={"reviewee_id": s_user_id, "rating": 4, "comment": "Actually, it was decent, 4 stars."},
            headers={"Authorization": f"Bearer {c_tok}"}
        )
        self.assertEqual(res_update.status_code, 200)
        self.assertEqual(res_update.json["rating"], 4)
        self.assertEqual(res_update.json["comment"], "Actually, it was decent, 4 stars.")

        # Verify FreelancerProfile updates accordingly
        db.session.refresh(prof)
        self.assertEqual(prof.rating_count, 1)
        self.assertEqual(prof.rating_avg, 4.0)


if __name__ == "__main__":
    unittest.main()
