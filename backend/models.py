"""SQLAlchemy database models for SkillSwap."""
from datetime import datetime
from backend.extensions import db


class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    users = db.relationship("User", back_populates="role")


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    campus = db.Column(db.String(120))
    profile_picture = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)
    is_banned = db.Column(db.Boolean, default=False)
    is_online = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    wallet_balance = db.Column(db.Numeric(10, 2), default=1000.00)

    role = db.relationship("Role", back_populates="users")
    freelancer_profile = db.relationship("FreelancerProfile", back_populates="user", uselist=False)
    public_profile = db.relationship("PublicProfile", back_populates="user", uselist=False, foreign_keys="PublicProfile.user_id")
    projects_posted = db.relationship("Project", back_populates="client", foreign_keys="Project.client_id")
    applications = db.relationship("Application", back_populates="applicant")
    reviews_given = db.relationship("Review", back_populates="reviewer", foreign_keys="Review.reviewer_id")
    notifications = db.relationship("Notification", back_populates="user")

    def to_dict(self, include_email=False):
        data = {
            "id": self.id,
            "full_name": self.full_name,
            "role": self.role.name if self.role else None,
            "campus": self.campus,
            "profile_picture": self.profile_picture,
            "is_online": self.is_online,
            "wallet_balance": float(self.wallet_balance or 0),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_email:
            data["email"] = self.email
        return data


class FreelancerProfile(db.Model):
    __tablename__ = "freelancer_profiles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)
    bio = db.Column(db.Text)
    headline = db.Column(db.String(200))
    hourly_rate = db.Column(db.Numeric(10, 2), default=0)
    availability = db.Column(db.String(50), default="available")
    github_url = db.Column(db.String(255))
    linkedin_url = db.Column(db.String(255))
    resume_path = db.Column(db.String(255))
    ai_summary = db.Column(db.Text)
    rating_avg = db.Column(db.Float, default=0.0)
    rating_count = db.Column(db.Integer, default=0)
    total_earnings = db.Column(db.Numeric(12, 2), default=0)
    is_verified = db.Column(db.Boolean, default=False)
    is_featured = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # LinkedIn-style rich professional sections
    work_experience = db.Column(db.Text, default="")
    education = db.Column(db.Text, default="")

    # Trust Score Metrics
    trust_score = db.Column(db.Float, default=95.0)
    completion_rate = db.Column(db.Float, default=100.0)
    response_speed = db.Column(db.Float, default=98.0)
    delivery_consistency = db.Column(db.Float, default=96.0)
    communication_score = db.Column(db.Float, default=97.0)
    ai_reliability_score = db.Column(db.Float, default=95.0)

    # Gamification Parameters
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.String(50), default="Rookie")
    streak_days = db.Column(db.Integer, default=0)

    user = db.relationship("User", back_populates="freelancer_profile")
    skills = db.relationship("UserSkill", back_populates="profile", cascade="all, delete-orphan")
    portfolio_items = db.relationship("PortfolioItem", back_populates="profile", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "bio": self.bio,
            "headline": self.headline,
            "hourly_rate": float(self.hourly_rate or 0),
            "availability": self.availability,
            "github_url": self.github_url,
            "linkedin_url": self.linkedin_url,
            "resume_path": self.resume_path,
            "ai_summary": self.ai_summary,
            "rating_avg": self.rating_avg,
            "rating_count": self.rating_count,
            "total_earnings": float(self.total_earnings or 0),
            "is_verified": self.is_verified,
            "is_featured": self.is_featured,
            
            # LinkedIn columns
            "work_experience": self.work_experience or "",
            "education": self.education or "",
            
            # Trust score dict mappings
            "trust_score": self.trust_score or 95.0,
            "completion_rate": self.completion_rate or 100.0,
            "response_speed": self.response_speed or 98.0,
            "delivery_consistency": self.delivery_consistency or 96.0,
            "communication_score": self.communication_score or 97.0,
            "ai_reliability_score": self.ai_reliability_score or 95.0,
            
            # Gamification
            "xp": self.xp or 0,
            "level": self.level or "Rookie",
            "streak_days": self.streak_days or 0,

            "skills": [s.to_dict() for s in self.skills],
            "user": self.user.to_dict() if self.user else None,
        }


class Skill(db.Model):
    __tablename__ = "skills"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))

    user_skills = db.relationship("UserSkill", back_populates="skill")


class UserSkill(db.Model):
    __tablename__ = "user_skills"
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("freelancer_profiles.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"), nullable=False)
    proficiency = db.Column(db.String(30), default="intermediate")
    is_verified = db.Column(db.Boolean, default=False)

    profile = db.relationship("FreelancerProfile", back_populates="skills")
    skill = db.relationship("Skill", back_populates="user_skills")

    def to_dict(self):
        return {
            "id": self.id,
            "skill_id": self.skill_id,
            "name": self.skill.name if self.skill else None,
            "proficiency": self.proficiency,
            "is_verified": self.is_verified,
        }


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False)
    icon = db.Column(db.String(50), default="briefcase")
    projects = db.relationship("Project", back_populates="category")


class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    budget = db.Column(db.Numeric(10, 2), nullable=False)
    deadline = db.Column(db.Date)
    
    # Supported status lifecycle: Draft, Open, Under Review, Hiring, In Progress, Submitted, Revision Requested, Completed, Cancelled, Disputed
    status = db.Column(db.String(30), default="open", index=True)
    skills_required = db.Column(db.Text)
    is_featured = db.Column(db.Boolean, default=False)
    hired_freelancer_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id"))
    progress = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Advanced Job Posting fields
    project_type = db.Column(db.String(50), default="freelance")  # freelance, internship, contest
    experience_level = db.Column(db.String(50), default="intermediate")  # entry, intermediate, expert
    remote_onsite = db.Column(db.String(50), default="remote")  # remote, onsite, hybrid
    is_urgent = db.Column(db.Boolean, default=False)
    duration = db.Column(db.String(100))
    team_size = db.Column(db.Integer, default=1)
    tags = db.Column(db.String(255))
    attachments = db.Column(db.String(255))

    client = db.relationship("User", back_populates="projects_posted", foreign_keys=[client_id])
    category = db.relationship("Category", back_populates="projects")
    applications = db.relationship("Application", back_populates="project", cascade="all, delete-orphan")
    team = db.relationship("Team", back_populates="projects", foreign_keys=[team_id])

    def to_dict(self):
        return {
            "id": self.id,
            "client_id": self.client_id,
            "client_name": self.client.full_name if self.client else None,
            "category_id": self.category_id,
            "category": self.category.name if self.category else None,
            "title": self.title,
            "description": self.description,
            "budget": float(self.budget),
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "status": self.status,
            "skills_required": self.skills_required,
            "is_featured": self.is_featured,
            "progress": self.progress,
            "hired_freelancer_id": self.hired_freelancer_id,
            "team_id": self.team_id,
            "team_name": self.team.name if self.team else None,
            "application_count": len(self.applications),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "project_type": self.project_type,
            "experience_level": self.experience_level,
            "remote_onsite": self.remote_onsite,
            "is_urgent": self.is_urgent,
            "duration": self.duration,
            "team_size": self.team_size,
            "tags": self.tags,
            "attachments": self.attachments,
        }


class Application(db.Model):
    __tablename__ = "applications"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False, index=True)
    applicant_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    cover_letter = db.Column(db.Text, nullable=False)
    proposed_rate = db.Column(db.Numeric(10, 2))
    status = db.Column(db.String(30), default="pending", index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    project = db.relationship("Project", back_populates="applications")
    applicant = db.relationship("User", back_populates="applications")

    def to_dict(self):
        # Use pre-loaded relationship data (avoids N+1 queries when joinedload is used)
        fp = self.applicant.freelancer_profile if self.applicant else None
        pub = self.applicant.public_profile if self.applicant else None
        pub_slug = pub.slug if pub else None

        return {
            "id": self.id,
            "project_id": self.project_id,
            "project_title": self.project.title if self.project else None,
            "applicant_id": self.applicant_id,
            "applicant_name": self.applicant.full_name if self.applicant else None,
            "applicant_headline": fp.headline if fp else None,
            "applicant_level": fp.level if fp else "Rookie",
            "applicant_rating_avg": round(float(fp.rating_avg), 1) if fp and fp.rating_avg else 0.0,
            "applicant_rating_count": fp.rating_count if fp else 0,
            "applicant_slug": pub_slug,
            "cover_letter": self.cover_letter,
            "proposed_rate": float(self.proposed_rate) if self.proposed_rate else None,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Conversation(db.Model):
    __tablename__ = "conversations"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"))
    participant_one = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    participant_two = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    messages = db.relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey("conversations.id"), nullable=False, index=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    conversation = db.relationship("Conversation", back_populates="messages")
    sender = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "sender_id": self.sender_id,
            "sender_name": self.sender.full_name if self.sender else None,
            "content": self.content,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    type = db.Column(db.String(50), default="info")
    link = db.Column(db.String(255))
    priority = db.Column(db.String(20), default="normal")  # normal, low, high
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="notifications")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "type": self.type,
            "link": self.link,
            "priority": self.priority,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Review(db.Model):
    __tablename__ = "reviews"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    reviewee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    reviewer = db.relationship("User", back_populates="reviews_given", foreign_keys=[reviewer_id])

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "reviewer_id": self.reviewer_id,
            "reviewer_name": self.reviewer.full_name if self.reviewer else None,
            "reviewee_id": self.reviewee_id,
            "rating": self.rating,
            "comment": self.comment,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Payment(db.Model):
    __tablename__ = "payments"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    payer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    payee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    
    # status: pending, escrowed, completed, disputed, refunded
    status = db.Column(db.String(30), default="pending")
    milestone = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "payer_id": self.payer_id,
            "payee_id": self.payee_id,
            "amount": float(self.amount),
            "status": self.status,
            "milestone": self.milestone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class PortfolioItem(db.Model):
    __tablename__ = "portfolio_items"
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("freelancer_profiles.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    image_path = db.Column(db.String(255))
    project_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    profile = db.relationship("FreelancerProfile", back_populates="portfolio_items")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "image_path": self.image_path,
            "project_url": self.project_url,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ActivityLog(db.Model):
    __tablename__ = "activity_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Report(db.Model):
    __tablename__ = "reports"
    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    reported_user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"))
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), default="open")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "reporter_id": self.reporter_id,
            "reported_user_id": self.reported_user_id,
            "project_id": self.project_id,
            "reason": self.reason,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class VerificationRequest(db.Model):
    __tablename__ = "verification_requests"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey("skills.id"))
    document_path = db.Column(db.String(255))
    status = db.Column(db.String(30), default="pending")
    admin_note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "skill_id": self.skill_id,
            "document_path": self.document_path,
            "status": self.status,
            "admin_note": self.admin_note,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SavedJob(db.Model):
    __tablename__ = "saved_jobs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("user_id", "project_id", name="uq_saved_job"),)


class SavedFreelancer(db.Model):
    __tablename__ = "saved_freelancers"
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    freelancer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("client_id", "freelancer_id", name="uq_saved_freelancer"),)


# =========================================================================
# NEW SYSTEM EXTENSIONS: CHATWORK, KANBAN, XP, DISPUTES, INTERVIEWS, COMPETITIONS
# =========================================================================

class ProjectTimelineEvent(db.Model):
    __tablename__ = "project_timeline_events"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    status = db.Column(db.String(30), nullable=False)
    action_by_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    details = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "status": self.status,
            "action_by_id": self.action_by_id,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Achievement(db.Model):
    __tablename__ = "achievements"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    badge_icon = db.Column(db.String(50), default="🏆")
    unlocked_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "badge_icon": self.badge_icon,
            "unlocked_at": self.unlocked_at.isoformat() if self.unlocked_at else None,
        }


class Dispute(db.Model):
    __tablename__ = "disputes"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    evidence_url = db.Column(db.String(255))
    status = db.Column(db.String(30), default="open")  # open, resolved, refunded
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "reporter_id": self.reporter_id,
            "title": self.title,
            "reason": self.reason,
            "evidence_url": self.evidence_url,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class KanbanTask(db.Model):
    __tablename__ = "kanban_tasks"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    column = db.Column(db.String(30), default="todo")  # todo, in_progress, review, done
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "title": self.title,
            "description": self.description,
            "column": self.column,
            "assigned_to_id": self.assigned_to_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SharedFile(db.Model):
    __tablename__ = "shared_files"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    filename = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "filename": self.filename,
            "file_path": self.file_path,
            "uploaded_by_id": self.uploaded_by_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AIInterview(db.Model):
    __tablename__ = "ai_interviews"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    skill_name = db.Column(db.String(80), nullable=False)
    score = db.Column(db.Integer, default=0)
    evaluation_report = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "skill_name": self.skill_name,
            "score": self.score,
            "evaluation_report": self.evaluation_report,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Hackathon(db.Model):
    __tablename__ = "hackathons"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    prize_pool = db.Column(db.Numeric(10, 2), default=0)
    deadline = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "prize_pool": float(self.prize_pool),
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Team(db.Model):
    __tablename__ = "teams"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    creator = db.relationship("User", foreign_keys=[created_by])
    members = db.relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    invitations = db.relationship("TeamInvitation", back_populates="team", cascade="all, delete-orphan")
    messages = db.relationship("TeamMessage", back_populates="team", cascade="all, delete-orphan")
    projects = db.relationship("Project", back_populates="team")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_by": self.created_by,
            "created_by_name": self.creator.full_name if self.creator else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "members": [m.to_dict() for m in self.members]
        }


class TeamMember(db.Model):
    __tablename__ = "team_members"
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = db.Column(db.String(50), default="Frontend Developer")
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    team = db.relationship("Team", back_populates="members")
    user = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "team_id": self.team_id,
            "user_id": self.user_id,
            "user_name": self.user.full_name if self.user else None,
            "user_email": self.user.email if self.user else None,
            "role": self.role,
            "joined_at": self.joined_at.isoformat() if self.joined_at else None
        }


class TeamInvitation(db.Model):
    __tablename__ = "team_invitations"
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(30), default="pending")  # pending, accepted, rejected

    team = db.relationship("Team", back_populates="invitations")
    sender = db.relationship("User", foreign_keys=[sender_id])
    receiver = db.relationship("User", foreign_keys=[receiver_id])

    def to_dict(self):
        return {
            "id": self.id,
            "team_id": self.team_id,
            "team_name": self.team.name if self.team else None,
            "sender_id": self.sender_id,
            "sender_name": self.sender.full_name if self.sender else None,
            "receiver_id": self.receiver_id,
            "receiver_name": self.receiver.full_name if self.receiver else None,
            "status": self.status
        }


class TeamMessage(db.Model):
    __tablename__ = "team_messages"
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    team = db.relationship("Team", back_populates="messages")
    sender = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "team_id": self.team_id,
            "sender_id": self.sender_id,
            "sender_name": self.sender.full_name if self.sender else None,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class PublicProfile(db.Model):
    __tablename__ = "public_profiles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    slug = db.Column(db.String(120), unique=True, index=True, nullable=False)
    bio = db.Column(db.Text)
    github_url = db.Column(db.String(255))
    linkedin_url = db.Column(db.String(255))
    portfolio_views = db.Column(db.Integer, default=0)

    user = db.relationship("User", back_populates="public_profile")
    projects = db.relationship("PortfolioProject", back_populates="profile", cascade="all, delete-orphan")
    reviews = db.relationship("ProfileReview", back_populates="profile", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "slug": self.slug,
            "bio": self.bio,
            "github_url": self.github_url,
            "linkedin_url": self.linkedin_url,
            "portfolio_views": self.portfolio_views,
            "user": self.user.to_dict() if self.user else None,
            "projects": [p.to_dict() for p in self.projects],
            "reviews": [r.to_dict() for r in self.reviews]
        }


class PortfolioProject(db.Model):
    __tablename__ = "portfolio_projects"
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("public_profiles.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)
    image = db.Column(db.String(255))
    technologies = db.Column(db.String(255))
    live_demo_url = db.Column(db.String(255))

    profile = db.relationship("PublicProfile", back_populates="projects")

    def to_dict(self):
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "title": self.title,
            "description": self.description,
            "image": self.image,
            "technologies": self.technologies,
            "live_demo_url": self.live_demo_url
        }


class ProfileReview(db.Model):
    __tablename__ = "profile_reviews"
    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("public_profiles.id", ondelete="CASCADE"), nullable=False)
    reviewer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)

    profile = db.relationship("PublicProfile", back_populates="reviews")
    reviewer = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "reviewer_id": self.reviewer_id,
            "reviewer_name": self.reviewer.full_name if self.reviewer else None,
            "rating": self.rating,
            "comment": self.comment
        }


# =========================================================================
# VIRTUAL WALLET, ESCROW, AND FINANCIAL TRANSACTION MODELS (ADVANCED MODULE)
# =========================================================================

class Wallet(db.Model):
    __tablename__ = "wallets"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    balance = db.Column(db.Numeric(10, 2), default=0.00)
    pending_balance = db.Column(db.Numeric(10, 2), default=0.00)
    total_earned = db.Column(db.Numeric(10, 2), default=0.00)
    total_spent = db.Column(db.Numeric(10, 2), default=0.00)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", backref=db.backref("wallet", uselist=False, cascade="all, delete-orphan"))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "balance": float(self.balance),
            "pending_balance": float(self.pending_balance),
            "total_earned": float(self.total_earned),
            "total_spent": float(self.total_spent),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class Transaction(db.Model):
    __tablename__ = "transactions"
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # deposit, escrow_lock, escrow_release, withdrawal, refund
    status = db.Column(db.String(30), default="pending")  # pending, completed, failed
    reference_code = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship("User", foreign_keys=[sender_id])
    receiver = db.relationship("User", foreign_keys=[receiver_id])

    def to_dict(self):
        return {
            "id": self.id,
            "sender_id": self.sender_id,
            "sender_name": self.sender.full_name if self.sender else "Platform",
            "receiver_id": self.receiver_id,
            "receiver_name": self.receiver.full_name if self.receiver else "Platform/Bank",
            "amount": float(self.amount),
            "type": self.type,
            "status": self.status,
            "reference_code": self.reference_code,
            "description": self.description,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class EscrowPayment(db.Model):
    __tablename__ = "escrow_payments"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    freelancer_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(30), default="pending")  # Pending, Escrowed, Submitted, Released, Refunded, Disputed, Cancelled
    milestone = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    released_at = db.Column(db.DateTime, nullable=True)

    project = db.relationship("Project")
    client = db.relationship("User", foreign_keys=[client_id])
    freelancer = db.relationship("User", foreign_keys=[freelancer_id])

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "project_title": self.project.title if self.project else "N/A",
            "project_status": self.project.status if self.project else "N/A",
            "client_id": self.client_id,
            "client_name": self.client.full_name if self.client else "Client",
            "freelancer_id": self.freelancer_id,
            "freelancer_name": self.freelancer.full_name if self.freelancer else "Freelancer",
            "amount": float(self.amount),
            "status": self.status,
            "milestone": self.milestone,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "released_at": self.released_at.isoformat() if self.released_at else None
        }


class WithdrawalRequest(db.Model):
    __tablename__ = "withdrawal_requests"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    method = db.Column(db.String(50), nullable=False)  # PayPal, Bank Transfer, Venmo
    status = db.Column(db.String(30), default="pending")  # Pending, Approved, Rejected, Processed
    requested_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_name": self.user.full_name if self.user else "User",
            "amount": float(self.amount),
            "method": self.method,
            "status": self.status,
            "requested_at": self.requested_at.isoformat() if self.requested_at else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None
        }


class PaymentNotification(db.Model):
    __tablename__ = "payment_notifications"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User")

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "message": self.message,
            "is_read": self.is_read,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
