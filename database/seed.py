"""Seed database with an extensive simulation of 10 students, 10 clients, and rich multi-user freelance interactions."""
import os
import sys
from datetime import date, timedelta, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app import create_app
from backend.extensions import db
from backend.models import (
    Role, User, FreelancerProfile, Skill, UserSkill,
    Category, Project, Application, Achievement, KanbanTask, Hackathon, ProjectTimelineEvent,
    Team, TeamMember, TeamInvitation, TeamMessage, PublicProfile, PortfolioProject, ProfileReview,
    Wallet, Transaction, EscrowPayment, WithdrawalRequest, PaymentNotification, Dispute, Message, Conversation
)
from backend.utils import hash_password


def seed():
    app = create_app()
    with app.app_context():
        print("Cleaning and rebuilding SQLite database tables...")
        db.drop_all()
        db.create_all()

        # 1. Seed Roles
        print("Seeding roles...")
        student_role = Role(name="student")
        client_role = Role(name="client")
        admin_role = Role(name="admin")
        db.session.add_all([student_role, client_role, admin_role])
        db.session.commit()

        # 2. Seed Categories
        print("Seeding project categories...")
        cat_dev = Category(name="Development & Tech", slug="dev-tech", icon="code")
        cat_design = Category(name="Design & Creative", slug="design-creative", icon="palette")
        cat_writing = Category(name="Content & Writing", slug="content-writing", icon="pen")
        cat_marketing = Category(name="Marketing", slug="marketing", icon="megaphone")
        cat_academic = Category(name="Academic Services", slug="academic-services", icon="book")
        cat_ai = Category(name="AI & Automation", slug="ai-automation", icon="cpu")
        cat_media = Category(name="Media Production", slug="media-production", icon="video")
        cat_analytics = Category(name="Data & Analytics", slug="data-analytics", icon="chart-bar")
        
        db.session.add_all([
            cat_dev, cat_design, cat_writing, cat_marketing,
            cat_academic, cat_ai, cat_media, cat_analytics
        ])
        db.session.commit()

        # Backward compatibility aliases for existing seeder code
        cat_tutoring = cat_academic
        cat_webdev = cat_dev
        cat_data = cat_analytics

        # 3. Seed Skills
        print("Seeding skills pool...")
        skills = {
            "Python": Skill(name="Python", category_id=cat_dev.id),
            "React": Skill(name="React", category_id=cat_dev.id),
            "UI Design": Skill(name="UI Design", category_id=cat_design.id),
            "Figma": Skill(name="Figma", category_id=cat_design.id),
            "Writing": Skill(name="Writing", category_id=cat_writing.id),
            "CS101": Skill(name="CS101", category_id=cat_academic.id),
            "Data Science": Skill(name="Data Science", category_id=cat_analytics.id),
            "Calculus": Skill(name="Calculus", category_id=cat_academic.id),
            "Web Scraping": Skill(name="Web Scraping", category_id=cat_dev.id),
            "Copywriting": Skill(name="Copywriting", category_id=cat_writing.id)
        }
        db.session.add_all(skills.values())
        db.session.commit()

        # 4. Seed Platform Administrator
        print("Seeding platform admin...")
        admin = User(
            email="admin@skillswap.edu",
            password_hash=hash_password("Admin123!"),
            full_name="Platform Admin",
            role_id=admin_role.id,
            campus="HQ",
            wallet_balance=100000.00
        )
        db.session.add(admin)
        db.session.flush()

        # Admin Wallet
        db.session.add(Wallet(
            user_id=admin.id,
            balance=100000.00,
            pending_balance=0.00,
            total_earned=100000.00,
            total_spent=0.00
        ))

        # 5. Seed 10 Students (Freelancers)
        print("Seeding 10 freelancers (students)...")
        students_data = [
            ("alex@campus.edu", "Alex Chen", "alex-chen", "MIT", "Elite Engineer", "Passionate Full Stack Developer specializing in Flask, React, and databases.", 3400, 6, 25.00, 98.2, 450.00),
            ("sam@campus.edu", "Sam Rivera", "sam-rivera", "Stanford", "Senior Designer", "Creative UI/UX Designer crafting premium glowing dark mode portfolios.", 2100, 4, 30.00, 96.5, 300.00),
            ("leo@campus.edu", "Leo Vance", "leo-vance", "Berkeley", "Rising Star", "Junior Frontend Developer focused on HTML/CSS and Vanilla JS.", 850, 1, 15.00, 95.0, 150.00),
            ("mia@campus.edu", "Mia Wong", "mia-wong", "Columbia", "Pro Writer", "Professional academic editor and technical copywriter.", 1400, 3, 20.00, 97.0, 200.00),
            ("raj@campus.edu", "Raj Patel", "raj-patel", "Yale", "Star Tutor", "Data Analyst and experienced tutor for calculus and python regressions.", 980, 2, 18.00, 94.0, 120.00),
            ("emma@campus.edu", "Emma Watson", "emma-watson", "Caltech", "Python Dev", "Enthusiastic python dev specialized in web scraping, BeautifulSoup, and automations.", 1200, 3, 22.00, 96.0, 180.00),
            ("liam@campus.edu", "Liam Davis", "liam-davis", "NYU", "Graphics Expert", "Digital illustrator producing modern banners, logos, and vector assets.", 1550, 4, 25.00, 95.5, 220.00),
            ("sophia@campus.edu", "Sophia Martinez", "sophia-martinez", "UCLA", "SEO Copywriter", "SEO blogging, newsletter copy, and creative campus advertisement briefs.", 1100, 2, 18.00, 96.2, 140.00),
            ("noah@campus.edu", "Noah Wilson", "noah-wilson", "Harvard", "Frontend Dev", "React.js enthusiast focused on interactive charts and complex web layouts.", 1750, 5, 28.00, 97.5, 260.00),
            ("olivia@campus.edu", "Olivia Taylor", "olivia-taylor", "Princeton", "Math Genius", "Experienced peer tutor specialized in college calculus and linear algebra.", 1600, 4, 20.00, 98.0, 210.00)
        ]

        students = {}
        for email, name, slug, campus, level, bio, xp, streak, rate, trust, balance in students_data:
            s_user = User(
                email=email,
                password_hash=hash_password("Demo123!"),
                full_name=name,
                role_id=student_role.id,
                campus=campus,
                wallet_balance=balance
            )
            db.session.add(s_user)
            db.session.flush()
            students[email] = s_user

            # Wallet for Student
            db.session.add(Wallet(
                user_id=s_user.id,
                balance=balance,
                pending_balance=0.00,
                total_earned=balance * 2.5,
                total_spent=50.00
            ))

            # Freelancer Profile
            f_prof = FreelancerProfile(
                user_id=s_user.id,
                headline=f"{name} - {level}",
                bio=bio,
                hourly_rate=rate,
                availability="available",
                rating_avg=4.9,
                rating_count=8,
                total_earnings=balance * 2.5,
                is_verified=True,
                trust_score=trust,
                completion_rate=100.0,
                response_speed=98.0,
                delivery_consistency=97.0,
                communication_score=96.0,
                ai_reliability_score=trust,
                xp=xp,
                level=level,
                streak_days=streak
            )
            db.session.add(f_prof)
            db.session.flush()

            # Public Showcase Profile
            pub_prof = PublicProfile(
                user_id=s_user.id,
                slug=slug,
                bio=bio,
                github_url=f"https://github.com/{slug}",
                linkedin_url=f"https://linkedin.com/in/{slug}",
                portfolio_views=140 + xp // 10
            )
            db.session.add(pub_prof)
            db.session.flush()

            # Portfolio Project
            db.session.add(PortfolioProject(
                profile_id=pub_prof.id,
                title=f"Signature Work - {name}",
                description=f"A beautiful production-grade portfolio showcase build detailing modern methods.",
                image=f"/frontend/assets/projects/{slug}.png",
                technologies="Python, Javascript, CSS",
                live_demo_url="https://skillswap.edu"
            ))

            # Assign primary skill mappings
            if "Engineer" in level or "Dev" in level:
                db.session.add(UserSkill(profile_id=f_prof.id, skill_id=skills["Python"].id, proficiency="expert", is_verified=True))
                db.session.add(UserSkill(profile_id=f_prof.id, skill_id=skills["React"].id, proficiency="advanced", is_verified=True))
                db.session.add(UserSkill(profile_id=f_prof.id, skill_id=skills["Web Scraping"].id, proficiency="expert", is_verified=True))
            elif "Designer" in level or "Graphics" in level:
                db.session.add(UserSkill(profile_id=f_prof.id, skill_id=skills["UI Design"].id, proficiency="expert", is_verified=True))
                db.session.add(UserSkill(profile_id=f_prof.id, skill_id=skills["Figma"].id, proficiency="expert", is_verified=True))
            elif "Writer" in level or "Copywriter" in level:
                db.session.add(UserSkill(profile_id=f_prof.id, skill_id=skills["Writing"].id, proficiency="expert", is_verified=True))
                db.session.add(UserSkill(profile_id=f_prof.id, skill_id=skills["Copywriting"].id, proficiency="expert", is_verified=True))
            elif "Tutor" in level or "Genius" in level:
                db.session.add(UserSkill(profile_id=f_prof.id, skill_id=skills["CS101"].id, proficiency="expert", is_verified=True))
                db.session.add(UserSkill(profile_id=f_prof.id, skill_id=skills["Calculus"].id, proficiency="expert", is_verified=True))
                db.session.add(UserSkill(profile_id=f_prof.id, skill_id=skills["Data Science"].id, proficiency="advanced", is_verified=True))

        db.session.commit()

        # 6. Seed 10 Clients (Job Posters)
        print("Seeding 10 clients...")
        clients_data = [
            ("jordan@campus.edu", "Jordan Lee", "Berkeley Startup Lab", 1500.00),
            ("evelyn@campus.edu", "Dr. Evelyn Vance", "MIT CS Department", 3000.00),
            ("chloe@campus.edu", "Chloe Martinez", "Stanford Student Council", 800.00),
            ("marcus@campus.edu", "Prof. Marcus Aurelius", "Harvard Philosophy Dept", 1200.00),
            ("diana@campus.edu", "Diana Prince", "Caltech Robotics Club", 1400.00),
            ("bruce@campus.edu", "Bruce Wayne", "Princeton Athletics Rep", 2500.00),
            ("clark@campus.edu", "Clark Kent", "Columbia Daily Campus", 950.00),
            ("selina@campus.edu", "Selina Kyle", "NYU Fine Arts Gallery", 1100.00),
            ("barry@campus.edu", "Barry Allen", "UCLA Physics Lab", 1350.00),
            ("arthur@campus.edu", "Arthur Curry", "Yale Marine Biology Assoc", 1000.00)
        ]

        clients = {}
        for email, name, campus, balance in clients_data:
            c_user = User(
                email=email,
                password_hash=hash_password("Demo123!"),
                full_name=name,
                role_id=client_role.id,
                campus=campus,
                wallet_balance=balance
            )
            db.session.add(c_user)
            db.session.flush()
            clients[email] = c_user

            # Wallet for Client
            db.session.add(Wallet(
                user_id=c_user.id,
                balance=balance,
                pending_balance=0.00,
                total_earned=0.00,
                total_spent=balance * 1.5
            ))
        db.session.commit()

        # 7. Seed Student Teams
        print("Seeding team collaboration structures...")
        dev_team = Team(
            name="DevSquad Alpha",
            description="Premium engineering student agency.",
            created_by=students["alex@campus.edu"].id
        )
        db.session.add(dev_team)
        db.session.flush()

        db.session.add(TeamMember(team_id=dev_team.id, user_id=students["alex@campus.edu"].id, role="Team Leader"))
        db.session.add(TeamMember(team_id=dev_team.id, user_id=students["sam@campus.edu"].id, role="UI/UX Designer"))
        db.session.add(TeamMember(team_id=dev_team.id, user_id=students["noah@campus.edu"].id, role="Frontend Developer"))
        db.session.add(TeamInvitation(team_id=dev_team.id, sender_id=students["alex@campus.edu"].id, receiver_id=students["sam@campus.edu"].id, status="accepted"))
        db.session.add(TeamInvitation(team_id=dev_team.id, sender_id=students["alex@campus.edu"].id, receiver_id=students["noah@campus.edu"].id, status="accepted"))

        # Seed Team Chats
        db.session.add(TeamMessage(team_id=dev_team.id, sender_id=students["alex@campus.edu"].id, message="Hey team! Let's build something beautiful today."))
        db.session.add(TeamMessage(team_id=dev_team.id, sender_id=students["sam@campus.edu"].id, message="Absolutely. Working on sleek glassmorphic icons."))
        db.session.add(TeamMessage(team_id=dev_team.id, sender_id=students["noah@campus.edu"].id, message="Count me in! I'll integrate the React dashboards."))
        db.session.commit()

        # 8. Seed Projects (Comprehensive Multi-User Interactions Lifecycle)
        print("Spawning 15 lifecycle-simulated projects and interactions...")

        # -------------------------------------------------------------
        # PHASE A: COMPLETED / SOLVED PROJECTS (6 projects)
        # -------------------------------------------------------------
        # Project 1
        p1 = Project(
            client_id=clients["jordan@campus.edu"].id, category_id=cat_tutoring.id,
            title="Python CS101 Midterm Prep Tutor",
            description="Need 1-on-1 peer tutoring on recursion, inheritance, and SQLite bindings.",
            budget=80.00, deadline=date.today() - timedelta(days=6), status="completed",
            skills_required="Python, CS101", hired_freelancer_id=students["alex@campus.edu"].id, progress=100
        )
        db.session.add(p1)
        db.session.flush()

        db.session.add(EscrowPayment(project_id=p1.id, client_id=clients["jordan@campus.edu"].id, freelancer_id=students["alex@campus.edu"].id, amount=80.00, status="Released", milestone="Midterm prep complete", released_at=datetime.utcnow() - timedelta(days=6)))
        db.session.add(Transaction(sender_id=clients["jordan@campus.edu"].id, receiver_id=None, amount=80.00, type="escrow_lock", status="completed", reference_code="TX-LOCK-1", description="Locked $80 for Python tutor"))
        db.session.add(Transaction(sender_id=None, receiver_id=students["alex@campus.edu"].id, amount=80.00, type="escrow_release", status="completed", reference_code="TX-RELS-1", description="Released $80 to Alex Chen"))
        db.session.add(ProfileReview(profile_id=PublicProfile.query.filter_by(user_id=students["alex@campus.edu"].id).first().id, reviewer_id=clients["jordan@campus.edu"].id, rating=5, comment="Alex is an amazing tutor! Cleared recursion easily."))

        # Project 2
        p2 = Project(
            client_id=clients["evelyn@campus.edu"].id, category_id=cat_writing.id,
            title="APA Citations Proofreading",
            description="Verify bibliography and citation formats for an academic submission.",
            budget=90.00, deadline=date.today() - timedelta(days=4), status="completed",
            skills_required="Writing", hired_freelancer_id=students["mia@campus.edu"].id, progress=100
        )
        db.session.add(p2)
        db.session.flush()

        db.session.add(EscrowPayment(project_id=p2.id, client_id=clients["evelyn@campus.edu"].id, freelancer_id=students["mia@campus.edu"].id, amount=90.00, status="Released", milestone="Bibliography complete", released_at=datetime.utcnow() - timedelta(days=4)))
        db.session.add(Transaction(sender_id=clients["evelyn@campus.edu"].id, receiver_id=None, amount=90.00, type="escrow_lock", status="completed", reference_code="TX-LOCK-2", description="Locked $90 for APA paper"))
        db.session.add(Transaction(sender_id=None, receiver_id=students["mia@campus.edu"].id, amount=90.00, type="escrow_release", status="completed", reference_code="TX-RELS-2", description="Released $90 to Mia Wong"))
        db.session.add(ProfileReview(profile_id=PublicProfile.query.filter_by(user_id=students["mia@campus.edu"].id).first().id, reviewer_id=clients["evelyn@campus.edu"].id, rating=5, comment="Perfect formatting. Exceptional attention to detail."))

        # Project 3
        p3 = Project(
            client_id=clients["diana@campus.edu"].id, category_id=cat_design.id,
            title="Robotics Club Website Redesign",
            description="Design modern glowing glass cards and a responsive Figma layout.",
            budget=150.00, deadline=date.today() - timedelta(days=3), status="completed",
            skills_required="Figma, UI Design", hired_freelancer_id=students["sam@campus.edu"].id, progress=100
        )
        db.session.add(p3)
        db.session.flush()

        db.session.add(EscrowPayment(project_id=p3.id, client_id=clients["diana@campus.edu"].id, freelancer_id=students["sam@campus.edu"].id, amount=150.00, status="Released", milestone="Figma mockups", released_at=datetime.utcnow() - timedelta(days=3)))
        db.session.add(Transaction(sender_id=clients["diana@campus.edu"].id, receiver_id=None, amount=150.00, type="escrow_lock", status="completed", reference_code="TX-LOCK-3", description="Locked $150 for Robotics UI"))
        db.session.add(Transaction(sender_id=None, receiver_id=students["sam@campus.edu"].id, amount=150.00, type="escrow_release", status="completed", reference_code="TX-RELS-3", description="Released $150 to Sam Rivera"))
        db.session.add(ProfileReview(profile_id=PublicProfile.query.filter_by(user_id=students["sam@campus.edu"].id).first().id, reviewer_id=clients["diana@campus.edu"].id, rating=5, comment="Stunning design work. Absolutely transformed our club's online presence."))

        # Project 4
        p4 = Project(
            client_id=clients["bruce@campus.edu"].id, category_id=cat_tutoring.id,
            title="Calculus II Exam Prep Tutor",
            description="Guide me through integrations and Taylor series approximations.",
            budget=70.00, deadline=date.today() - timedelta(days=2), status="completed",
            skills_required="Calculus", hired_freelancer_id=students["olivia@campus.edu"].id, progress=100
        )
        db.session.add(p4)
        db.session.flush()

        db.session.add(EscrowPayment(project_id=p4.id, client_id=clients["bruce@campus.edu"].id, freelancer_id=students["olivia@campus.edu"].id, amount=70.00, status="Released", milestone="Integrals session", released_at=datetime.utcnow() - timedelta(days=2)))
        db.session.add(Transaction(sender_id=clients["bruce@campus.edu"].id, receiver_id=None, amount=70.00, type="escrow_lock", status="completed", reference_code="TX-LOCK-4", description="Locked $70 for calculus tutor"))
        db.session.add(Transaction(sender_id=None, receiver_id=students["olivia@campus.edu"].id, amount=70.00, type="escrow_release", status="completed", reference_code="TX-RELS-4", description="Released $70 to Olivia Taylor"))
        db.session.add(ProfileReview(profile_id=PublicProfile.query.filter_by(user_id=students["olivia@campus.edu"].id).first().id, reviewer_id=clients["bruce@campus.edu"].id, rating=5, comment="Olivia made Taylor series seem easy! Acable prep."))

        # Project 5
        p5 = Project(
            client_id=clients["bruce@campus.edu"].id, category_id=cat_design.id,
            title="Vector Banner Graphics for Sports Meet",
            description="Design high-resolution posters and modern banner sets.",
            budget=60.00, deadline=date.today() - timedelta(days=1), status="completed",
            skills_required="Figma, UI Design", hired_freelancer_id=students["liam@campus.edu"].id, progress=100
        )
        db.session.add(p5)
        db.session.flush()

        db.session.add(EscrowPayment(project_id=p5.id, client_id=clients["bruce@campus.edu"].id, freelancer_id=students["liam@campus.edu"].id, amount=60.00, status="Released", milestone="Poster graphics", released_at=datetime.utcnow() - timedelta(days=1)))
        db.session.add(Transaction(sender_id=clients["bruce@campus.edu"].id, receiver_id=None, amount=60.00, type="escrow_lock", status="completed", reference_code="TX-LOCK-5", description="Locked $60 for banner design"))
        db.session.add(Transaction(sender_id=None, receiver_id=students["liam@campus.edu"].id, amount=60.00, type="escrow_release", status="completed", reference_code="TX-RELS-5", description="Released $60 to Liam Davis"))
        db.session.add(ProfileReview(profile_id=PublicProfile.query.filter_by(user_id=students["liam@campus.edu"].id).first().id, reviewer_id=clients["bruce@campus.edu"].id, rating=5, comment="Incredible speed and beautiful vectors! Strongly recommend Liam."))

        # Project 6
        p6 = Project(
            client_id=clients["marcus@campus.edu"].id, category_id=cat_writing.id,
            title="Philosophy Essay Bibliography Formatting",
            description="Clean and structure citation fields to Chicago manual style standards.",
            budget=40.00, deadline=date.today() - timedelta(days=1), status="completed",
            skills_required="Writing", hired_freelancer_id=students["mia@campus.edu"].id, progress=100
        )
        db.session.add(p6)
        db.session.flush()

        db.session.add(EscrowPayment(project_id=p6.id, client_id=clients["marcus@campus.edu"].id, freelancer_id=students["mia@campus.edu"].id, amount=40.00, status="Released", milestone="Chicago bibliography", released_at=datetime.utcnow() - timedelta(days=1)))
        db.session.add(Transaction(sender_id=clients["marcus@campus.edu"].id, receiver_id=None, amount=40.00, type="escrow_lock", status="completed", reference_code="TX-LOCK-6", description="Locked $40 for bibliography"))
        db.session.add(Transaction(sender_id=None, receiver_id=students["mia@campus.edu"].id, amount=40.00, type="escrow_release", status="completed", reference_code="TX-RELS-6", description="Released $40 to Mia Wong"))
        db.session.add(ProfileReview(profile_id=PublicProfile.query.filter_by(user_id=students["mia@campus.edu"].id).first().id, reviewer_id=clients["marcus@campus.edu"].id, rating=5, comment="A scholarly citation formatter. Absolute master of Chicago style!"))

        # -------------------------------------------------------------
        # PHASE B: ACTIVE / RUNNING PROJECTS (4 projects)
        # -------------------------------------------------------------
        # Project 7
        p7 = Project(
            client_id=clients["chloe@campus.edu"].id, category_id=cat_webdev.id,
            title="E-Commerce Landing Page with Obsidian Glass UI",
            description="Build a premium landing page with responsive glassmorphism modules.",
            budget=250.00, deadline=date.today() + timedelta(days=10), status="in_progress",
            skills_required="React, UI Design, CSS", hired_freelancer_id=students["alex@campus.edu"].id, progress=60, team_id=dev_team.id
        )
        db.session.add(p7)
        db.session.flush()

        db.session.add(EscrowPayment(project_id=p7.id, client_id=clients["chloe@campus.edu"].id, freelancer_id=students["alex@campus.edu"].id, amount=250.00, status="Escrowed", milestone="Frontend Component Assembly"))
        db.session.add(Transaction(sender_id=clients["chloe@campus.edu"].id, receiver_id=None, amount=250.00, type="escrow_lock", status="completed", reference_code="TX-LOCK-7", description="Locked $250 in escrow for Glass UI landing page"))

        db.session.add(KanbanTask(project_id=p7.id, title="UI/UX Wireframes", description="Design glass card grids.", column="done", assigned_to_id=students["alex@campus.edu"].id))
        db.session.add(KanbanTask(project_id=p7.id, title="Component Layout Coding", description="Assemble React CSS framework.", column="in_progress", assigned_to_id=students["alex@campus.edu"].id))
        db.session.add(KanbanTask(project_id=p7.id, title="Vercel Preview Deploy", description="Setup previews for client review.", column="todo", assigned_to_id=students["alex@campus.edu"].id))

        conv7 = Conversation(project_id=p7.id, participant_one=clients["chloe@campus.edu"].id, participant_two=students["alex@campus.edu"].id)
        db.session.add(conv7)
        db.session.flush()
        db.session.add(Message(conversation_id=conv7.id, sender_id=clients["chloe@campus.edu"].id, content="Hi Alex! How is the dashboard layout coming along? Can't wait to see the glass style."))
        db.session.add(Message(conversation_id=conv7.id, sender_id=students["alex@campus.edu"].id, content="Hey Chloe! The wireframes are finished. Working on compiling the responsive CSS grid tonight."))

        # Project 8
        p8 = Project(
            client_id=clients["clark@campus.edu"].id, category_id=cat_webdev.id,
            title="Campus News App React Frontend",
            description="Build a clean newspaper layout with article list routing.",
            budget=350.00, deadline=date.today() + timedelta(days=12), status="in_progress",
            skills_required="React, UI Design", hired_freelancer_id=students["noah@campus.edu"].id, progress=40
        )
        db.session.add(p8)
        db.session.flush()

        db.session.add(EscrowPayment(project_id=p8.id, client_id=clients["clark@campus.edu"].id, freelancer_id=students["noah@campus.edu"].id, amount=350.00, status="Escrowed", milestone="Article Router Grid"))
        db.session.add(Transaction(sender_id=clients["clark@campus.edu"].id, receiver_id=None, amount=350.00, type="escrow_lock", status="completed", reference_code="TX-LOCK-8", description="Locked $350 for News App"))

        db.session.add(KanbanTask(project_id=p8.id, title="React Router Setup", description="Link article feeds.", column="done", assigned_to_id=students["noah@campus.edu"].id))
        db.session.add(KanbanTask(project_id=p8.id, title="Feed Aggregation API", description="Render articles dynamically.", column="in_progress", assigned_to_id=students["noah@campus.edu"].id))

        conv8 = Conversation(project_id=p8.id, participant_one=clients["clark@campus.edu"].id, participant_two=students["noah@campus.edu"].id)
        db.session.add(conv8)
        db.session.flush()
        db.session.add(Message(conversation_id=conv8.id, sender_id=clients["clark@campus.edu"].id, content="Hey Noah, did we aggregate the database API feeds for the articles?"))
        db.session.add(Message(conversation_id=conv8.id, sender_id=students["noah@campus.edu"].id, content="Yes Clark! Router mappings are done. Working on fetching articles dynamically right now."))

        # Project 9
        p9 = Project(
            client_id=clients["barry@campus.edu"].id, category_id=cat_data.id,
            title="Physics Lab Experiment Data Cleaning",
            description="Sift through raw lab telemetry CSV files and build organized datasets.",
            budget=180.00, deadline=date.today() + timedelta(days=5), status="in_progress",
            skills_required="Data Science, Python", hired_freelancer_id=students["raj@campus.edu"].id, progress=50
        )
        db.session.add(p9)
        db.session.flush()

        db.session.add(EscrowPayment(project_id=p9.id, client_id=clients["barry@campus.edu"].id, freelancer_id=students["raj@campus.edu"].id, amount=180.00, status="Escrowed", milestone="Data filtration curves"))
        db.session.add(Transaction(sender_id=clients["barry@campus.edu"].id, receiver_id=None, amount=180.00, type="escrow_lock", status="completed", reference_code="TX-LOCK-9", description="Locked $180 for physics CSV curves"))

        conv9 = Conversation(project_id=p9.id, participant_one=clients["barry@campus.edu"].id, participant_two=students["raj@campus.edu"].id)
        db.session.add(conv9)
        db.session.flush()
        db.session.add(Message(conversation_id=conv9.id, sender_id=clients["barry@campus.edu"].id, content="Hi Raj, let me know when the anomaly filters are implemented in the Python scripts."))
        db.session.add(Message(conversation_id=conv9.id, sender_id=students["raj@campus.edu"].id, content="Hey Barry, filters are ready. Cleared 10,000 blank sensor coordinates! Plotted the curves just now."))

        # Project 10
        p10 = Project(
            client_id=clients["arthur@campus.edu"].id, category_id=cat_design.id,
            title="Marine Biology Club Logo Design",
            description="Create a marine-themed custom brand identity package and style guide.",
            budget=100.00, deadline=date.today() + timedelta(days=14), status="in_progress",
            skills_required="Figma, UI Design", hired_freelancer_id=students["sam@campus.edu"].id, progress=30
        )
        db.session.add(p10)
        db.session.flush()

        db.session.add(EscrowPayment(project_id=p10.id, client_id=clients["arthur@campus.edu"].id, freelancer_id=students["sam@campus.edu"].id, amount=100.00, status="Escrowed", milestone="Brand guidelines"))
        db.session.add(Transaction(sender_id=clients["arthur@campus.edu"].id, receiver_id=None, amount=100.00, type="escrow_lock", status="completed", reference_code="TX-LOCK-10", description="Locked $100 for Marine Logo"))

        # -------------------------------------------------------------
        # PHASE C: NEW / OPEN PROJECTS WITH BIDS (4 projects)
        # -------------------------------------------------------------
        # Project 11
        p11 = Project(
            client_id=clients["chloe@campus.edu"].id, category_id=cat_design.id,
            title="Student Association Logo & Brand Kit",
            description="Design vector files, secondary badge variations, and color guides.",
            budget=120.00, deadline=date.today() + timedelta(days=15), status="open",
            skills_required="Figma, UI Design", progress=0
        )
        db.session.add(p11)
        db.session.flush()

        db.session.add(Application(project_id=p11.id, applicant_id=students["sam@campus.edu"].id, cover_letter="I will design a beautiful vector branding package with multiple logo iterations, custom color palettes, and standard style guides.", proposed_rate=120.00, status="pending"))
        db.session.add(Application(project_id=p11.id, applicant_id=students["leo@campus.edu"].id, cover_letter="Junior designer with experience in campus gigs. Eager to design a great logo package quickly!", proposed_rate=100.00, status="pending"))

        # Project 12
        p12 = Project(
            client_id=clients["evelyn@campus.edu"].id, category_id=cat_webdev.id,
            title="Web Scraping for Academic Paper Research",
            description="Build python script to aggregate and parse JSON telemetry schedules from public pages.",
            budget=110.00, deadline=date.today() + timedelta(days=20), status="open",
            skills_required="Python, Web Scraping", progress=0
        )
        db.session.add(p12)
        db.session.flush()

        db.session.add(Application(project_id=p12.id, applicant_id=students["emma@campus.edu"].id, cover_letter="Web scraping is my main focus. I will deliver a clean Python script using BeautifulSoup and structured JSON files in 24 hours.", proposed_rate=110.00, status="pending"))
        db.session.add(Application(project_id=p12.id, applicant_id=students["alex@campus.edu"].id, cover_letter="Flask dev with experience writing fast scrapers with connection pools. Let's get this parsed.", proposed_rate=130.00, status="pending"))

        # Project 13
        p13 = Project(
            client_id=clients["barry@campus.edu"].id, category_id=cat_tutoring.id,
            title="Chemistry Lab PDF to Excel Data Entry",
            description="Quick transcription and scaling of chemical weight values.",
            budget=50.00, deadline=date.today() + timedelta(days=3), status="open",
            skills_required="Calculus", progress=0
        )
        db.session.add(p13)
        db.session.flush()

        db.session.add(Application(project_id=p13.id, applicant_id=students["leo@campus.edu"].id, cover_letter="Fast typing student eager to map out and clean all PDF weight values into Excel sheets.", proposed_rate=50.00, status="pending"))
        db.session.add(Application(project_id=p13.id, applicant_id=students["raj@campus.edu"].id, cover_letter="Data science student. I can write a quick pandas script to automate this transcription in 5 minutes.", proposed_rate=45.00, status="pending"))

        # Project 14
        p14 = Project(
            client_id=clients["clark@campus.edu"].id, category_id=cat_writing.id,
            title="Creative SEO Blog Writing for Campus Event",
            description="Write 3 engaging SEO-optimized articles about upcoming campus cultural events.",
            budget=80.00, deadline=date.today() + timedelta(days=7), status="open",
            skills_required="Writing", progress=0
        )
        db.session.add(p14)
        db.session.flush()

        db.session.add(Application(project_id=p14.id, applicant_id=students["sophia@campus.edu"].id, cover_letter="SEO copywriting student at UCLA. I will craft 3 highly engaging, searchable, and vibrant posts.", proposed_rate=80.00, status="pending"))
        db.session.add(Application(project_id=p14.id, applicant_id=students["mia@campus.edu"].id, cover_letter="Expert technical editor. Ready to structure and write high-quality posts.", proposed_rate=95.00, status="pending"))

        # -------------------------------------------------------------
        # PHASE D: DISPUTED PROJECTS (1 project)
        # -------------------------------------------------------------
        # Project 15
        p15 = Project(
            client_id=clients["jordan@campus.edu"].id, category_id=cat_data.id,
            title="ML Regression Project Data Cleaning",
            description="Need clean CSV files with scaled mathematical fields.",
            budget=150.00, deadline=date.today() - timedelta(days=3), status="disputed",
            skills_required="Data Science, Python", hired_freelancer_id=students["raj@campus.edu"].id, progress=40
        )
        db.session.add(p15)
        db.session.flush()

        db.session.add(EscrowPayment(project_id=p15.id, client_id=clients["jordan@campus.edu"].id, freelancer_id=students["raj@campus.edu"].id, amount=150.00, status="Disputed", milestone="Regression Data Cleanup"))
        db.session.add(Transaction(sender_id=clients["jordan@campus.edu"].id, receiver_id=None, amount=150.00, type="escrow_lock", status="completed", reference_code="TX-LOCK-15", description="Locked $150 for ML regressions"))
        db.session.add(Dispute(project_id=p15.id, reporter_id=clients["jordan@campus.edu"].id, title="Incomplete regressions and rawCSV errors", reason="Freelancer delivered random correlations instead of actual clean regression datasets. Requesting refund.", status="open"))

        # 9. Seed Financial Payouts (Withdrawals)
        print("Seeding financial payouts (withdrawals)...")
        db.session.add(WithdrawalRequest(user_id=students["alex@campus.edu"].id, amount=100.00, method="PayPal", status="Processed", approved_at=datetime.utcnow() - timedelta(days=2)))
        db.session.add(Transaction(sender_id=students["alex@campus.edu"].id, receiver_id=None, amount=100.00, type="withdrawal", status="completed", reference_code="TX-WITHDRAW-1", description="Processed $100.00 withdrawal to PayPal account."))

        db.session.add(WithdrawalRequest(user_id=students["sam@campus.edu"].id, amount=50.00, method="Bank Transfer", status="Processed", approved_at=datetime.utcnow() - timedelta(days=1)))
        db.session.add(Transaction(sender_id=students["sam@campus.edu"].id, receiver_id=None, amount=50.00, type="withdrawal", status="completed", reference_code="TX-WITHDRAW-2", description="Processed $50.00 withdrawal to Student Checking Account."))

        # 10. Seed Hackathons
        print("Seeding hackathons & assessments...")
        db.session.add(Hackathon(
            title="MIT HackFest 2026",
            description="Build solutions for green campuses. Sponsor booths and prizes by major tech companies.",
            prize_pool=2500.00,
            deadline=date.today() + timedelta(days=30)
        ))
        db.session.add(Hackathon(
            title="Stanford UI/UX Design Slam",
            description="Create the most gorgeous obsidian glassmorphism student profile system in 48 hours.",
            prize_pool=1000.00,
            deadline=date.today() + timedelta(days=45)
        ))

        # Commit everything!
        db.session.commit()
        print("SUCCESS: Epic 20-User Ecosystem Lifecycle database seed is complete!")


if __name__ == "__main__":
    seed()
