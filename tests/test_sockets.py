"""Automated integration tests for Flask-SocketIO realtime components."""
import os
import sys
import unittest
from datetime import datetime

# Append workspace path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from backend.extensions import db, socketio
from backend.models import User, Role, Project, Conversation, Message, Team, TeamMember, KanbanTask
from flask_jwt_extended import create_access_token


class SkillSwapSocketTests(unittest.TestCase):
    def setUp(self):
        """Setup isolated test SQLite context and seed data."""
        os.environ["TEST_DATABASE_URL"] = "sqlite:///test_sockets.db"
        self.app = create_app("testing")
        self.app.config["TESTING"] = True
        self.app.config["WTF_CSRF_ENABLED"] = False
        
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
        os.environ.pop("TEST_DATABASE_URL", None)
        if os.path.exists("test_sockets.db"):
            try:
                os.remove("test_sockets.db")
            except Exception:
                pass

    def _seed_data(self):
        """Seed roles, test users, and conversations."""
        # Roles
        student_role = Role.query.filter_by(name="student").first()
        if not student_role:
            student_role = Role(name="student")
            db.session.add(student_role)
            db.session.commit()

        client_role = Role.query.filter_by(name="client").first()
        if not client_role:
            client_role = Role(name="client")
            db.session.add(client_role)
            db.session.commit()

        # Users
        self.u1 = User.query.filter_by(email="sender@campus.edu").first()
        if not self.u1:
            self.u1 = User(
                email="sender@campus.edu",
                password_hash="Password123!",
                full_name="Alex Sender",
                role_id=student_role.id
            )
            db.session.add(self.u1)
            
        self.u2 = User.query.filter_by(email="receiver@campus.edu").first()
        if not self.u2:
            self.u2 = User(
                email="receiver@campus.edu",
                password_hash="Password123!",
                full_name="Jordan Receiver",
                role_id=client_role.id
            )
            db.session.add(self.u2)
            
        db.session.commit()
        self.u1_id = self.u1.id
        self.u2_id = self.u2.id

        # Conversation
        self.conv = Conversation(
            participant_one=self.u1_id,
            participant_two=self.u2_id
        )
        db.session.add(self.conv)
        db.session.commit()
        self.conv_id = self.conv.id

        # Team
        self.team = Team(name="Visual Development Team", created_by=self.u2_id)
        db.session.add(self.team)
        db.session.commit()
        self.team_id = self.team.id

        # Team Members
        m1 = TeamMember(team_id=self.team_id, user_id=self.u1_id, role="developer")
        m2 = TeamMember(team_id=self.team_id, user_id=self.u2_id, role="lead")
        db.session.add_all([m1, m2])
        db.session.commit()

        # Project
        self.proj = Project(
            client_id=self.u2_id,
            title="Design Obsidian Theme UI Project",
            description="Write core CSS variables",
            budget=300.00
        )
        db.session.add(self.proj)
        db.session.commit()

        # Kanban Task
        self.task = KanbanTask(
            project_id=self.proj.id,
            title="Design Obsidian Theme UI",
            description="Write core CSS variables",
            column="todo"
        )
        db.session.add(self.task)
        db.session.commit()
        self.task_id = self.task.id

    def test_authenticated_socket_connection(self):
        """Test Socket.IO handshake authentication using JWT credentials."""
        # 1. Test Unauthenticated Connection Rejected
        client_fail = socketio.test_client(self.app)
        self.assertFalse(client_fail.is_connected())

        # 2. Test Authenticated Connection Accepted
        token = create_access_token(identity=str(self.u1_id))
        client_ok = socketio.test_client(self.app, query_string=f"?token={token}")
        self.assertTrue(client_ok.is_connected())
        
        # Verify the "connected" event payload is successfully received
        received = client_ok.get_received()
        events = [r["name"] for r in received]
        self.assertIn("connected", events)

    def test_realtime_chat_broadcast_and_typing(self):
        """Test active room joining, new chat message emissions, and typing indicators."""
        # Establish Socket Client 1 (Alex)
        tok_1 = create_access_token(identity=str(self.u1_id))
        client_1 = socketio.test_client(self.app, query_string=f"?token={tok_1}")
        client_1.get_received() # Clear connect buffers

        # Establish Socket Client 2 (Jordan)
        tok_2 = create_access_token(identity=str(self.u2_id))
        client_2 = socketio.test_client(self.app, query_string=f"?token={tok_2}")
        client_2.get_received() # Clear connect buffers

        # 1. Join Conversation Room
        client_1.emit("join_conversation", {"conversation_id": self.conv_id})
        client_2.emit("join_conversation", {"conversation_id": self.conv_id})

        # 2. Test Typing Indicator Broadcasts (Client 1 starts typing)
        client_1.emit("typing", {"conversation_id": self.conv_id})
        
        # Verify Client 2 receives typing broadcast, while Client 1 does not (include_self=False)
        rec_2 = client_2.get_received()
        events_2 = [r["name"] for r in rec_2]
        self.assertIn("typing", events_2)
        
        rec_1 = client_1.get_received()
        events_1 = [r["name"] for r in rec_1]
        self.assertNotIn("typing", events_1)

        # 3. Test Message Emission & Room Broadcasts
        client_1.emit("send_message", {
            "conversation_id": self.conv_id,
            "content": "Hey Jordan, the obsidian design looks absolutely gorgeous!"
        })

        # Verify Client 2 receives new_message event and a visual browser alert notification
        rec_2_msg = client_2.get_received()
        msg_events = [r["name"] for r in rec_2_msg]
        self.assertIn("new_message", msg_events)
        self.assertIn("notification", msg_events)

    def test_collaborative_kanban_task_movement(self):
        """Test multi-user collaborative Kanban synchronizations on task column drag-and-drops."""
        tok_1 = create_access_token(identity=str(self.u1_id))
        client_1 = socketio.test_client(self.app, query_string=f"?token={tok_1}")
        
        tok_2 = create_access_token(identity=str(self.u2_id))
        client_2 = socketio.test_client(self.app, query_string=f"?token={tok_2}")

        client_1.emit("join_team", {"team_id": self.team_id})
        client_2.emit("join_team", {"team_id": self.team_id})
        
        client_1.get_received()
        client_2.get_received()

        # 1. Simulate Client 1 dragging task from 'todo' to 'in_progress'
        client_1.emit("move_team_task", {
            "team_id": self.team_id,
            "task_id": self.task_id,
            "column": "in_progress"
        })

        # 2. Verify column updates correctly in database
        db.session.expire_all()
        updated_task = KanbanTask.query.get(self.task_id)
        self.assertEqual(updated_task.column, "in_progress")

        # 3. Verify Client 2 receives immediate 'team_task_moved' synchronization broadcast
        rec_2 = client_2.get_received()
        events = [r["name"] for r in rec_2]
        self.assertIn("team_task_moved", events)
        
        # Verify details
        moved_event = next(r for r in rec_2 if r["name"] == "team_task_moved")
        self.assertEqual(moved_event["args"][0]["column"], "in_progress")
        self.assertEqual(moved_event["args"][0]["moved_by_name"], "Alex Sender")


if __name__ == "__main__":
    unittest.main()
