"""User and freelancer profile routes."""
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_
from sqlalchemy.orm import joinedload, selectinload
from backend.extensions import db
from backend.models import User, FreelancerProfile, Skill, UserSkill, PortfolioItem, SavedFreelancer
from backend.utils import save_upload, create_notification
from backend.middleware.security import sanitize_text, role_required, log_activity

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


@users_bp.route("/all", methods=["GET"])
@jwt_required()
def list_all_users():
    user_id = int(get_jwt_identity())
    users = User.query.filter(User.id != user_id, User.is_banned == False, User.is_active == True).all()
    result = []
    for u in users:
        result.append({
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role.name if u.role else "student",
            "campus": u.campus or ""
        })
    return jsonify(result)


@users_bp.route("/freelancers", methods=["GET"])
def list_freelancers():
    q = request.args.get("q", "")
    skill = request.args.get("skill", "")
    query = FreelancerProfile.query.join(User).filter(User.is_active == True, User.is_banned == False)
    if q:
        query = query.filter(or_(User.full_name.ilike(f"%{q}%"), FreelancerProfile.headline.ilike(f"%{q}%")))
    if skill:
        query = query.join(UserSkill).join(Skill).filter(Skill.name.ilike(f"%{skill}%"))
    profiles = query.options(
        joinedload(FreelancerProfile.user),
        selectinload(FreelancerProfile.skills).joinedload(UserSkill.skill)
    ).order_by(FreelancerProfile.is_featured.desc(), FreelancerProfile.rating_avg.desc()).limit(50).all()
    return jsonify([p.to_dict() for p in profiles])


@users_bp.route("/freelancers/<int:user_id>", methods=["GET"])
def get_freelancer(user_id):
    profile = FreelancerProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        return jsonify({"error": "Freelancer not found"}), 404
        
    data = profile.to_dict()
    # Fetch reviews received
    from backend.models import Review
    reviews = Review.query.filter_by(reviewee_id=user_id).order_by(Review.created_at.desc()).all()
    data["reviews"] = [r.to_dict() for r in reviews]
    
    return jsonify(data)


@users_bp.route("/profile", methods=["GET", "PUT"])
@jwt_required()
def my_profile():
    user = User.query.get(int(get_jwt_identity()))
    profile = user.freelancer_profile
    if request.method == "GET":
        if not profile:
            return jsonify({"error": "No freelancer profile"}), 404
        return jsonify(profile.to_dict())

    if not profile:
        profile = FreelancerProfile(user_id=user.id)
        db.session.add(profile)
    data = request.get_json() or {}
    profile.bio = sanitize_text(data.get("bio", profile.bio))
    profile.headline = sanitize_text(data.get("headline", profile.headline))
    profile.hourly_rate = data.get("hourly_rate", profile.hourly_rate)
    profile.availability = sanitize_text(data.get("availability", profile.availability))
    profile.github_url = sanitize_text(data.get("github_url", profile.github_url))
    profile.linkedin_url = sanitize_text(data.get("linkedin_url", profile.linkedin_url))
    profile.work_experience = sanitize_text(data.get("work_experience", profile.work_experience or ""))
    profile.education = sanitize_text(data.get("education", profile.education or ""))
    user.full_name = sanitize_text(data.get("full_name", user.full_name))
    user.campus = sanitize_text(data.get("campus", user.campus))
    db.session.commit()
    return jsonify({"message": "Profile updated", "profile": profile.to_dict()})


@users_bp.route("/profile/avatar", methods=["POST"])
@jwt_required()
def upload_avatar():
    user = User.query.get(int(get_jwt_identity()))
    file = request.files.get("file")
    try:
        path = save_upload(file, "profiles", current_app.config["ALLOWED_IMAGE_EXTENSIONS"])
        user.profile_picture = path
        db.session.commit()
        return jsonify({"message": "Avatar uploaded", "profile_picture": path})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@users_bp.route("/profile/resume", methods=["POST"])
@jwt_required()
@role_required("student")
def upload_resume():
    user = User.query.get(int(get_jwt_identity()))
    file = request.files.get("file")
    try:
        path = save_upload(file, "resumes", current_app.config["ALLOWED_DOC_EXTENSIONS"])
        user.freelancer_profile.resume_path = path
        db.session.commit()
        return jsonify({"message": "Resume uploaded", "resume_path": path})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@users_bp.route("/skills", methods=["GET", "POST"])
@jwt_required()
@role_required("student")
def manage_skills():
    user = User.query.get(int(get_jwt_identity()))
    profile = user.freelancer_profile
    if request.method == "GET":
        return jsonify([s.to_dict() for s in profile.skills])

    data = request.get_json() or {}
    skill_name = sanitize_text(data.get("name", "")).strip()
    proficiency = sanitize_text(data.get("proficiency", "intermediate"))
    if not skill_name:
        return jsonify({"error": "Skill name required"}), 400
    skill = Skill.query.filter_by(name=skill_name).first()
    if not skill:
        skill = Skill(name=skill_name)
        db.session.add(skill)
        db.session.flush()
    existing = UserSkill.query.filter_by(profile_id=profile.id, skill_id=skill.id).first()
    if existing:
        return jsonify({"error": "Skill already added"}), 409
    us = UserSkill(profile_id=profile.id, skill_id=skill.id, proficiency=proficiency)
    db.session.add(us)
    db.session.commit()
    return jsonify(us.to_dict()), 201


@users_bp.route("/skills/<int:skill_id>", methods=["DELETE"])
@jwt_required()
@role_required("student")
def delete_skill(skill_id):
    user = User.query.get(int(get_jwt_identity()))
    us = UserSkill.query.filter_by(profile_id=user.freelancer_profile.id, skill_id=skill_id).first()
    if not us:
        return jsonify({"error": "Skill not found"}), 404
    db.session.delete(us)
    db.session.commit()
    return jsonify({"message": "Skill removed"})


@users_bp.route("/portfolio", methods=["GET", "POST"])
@jwt_required()
@role_required("student")
def portfolio():
    user = User.query.get(int(get_jwt_identity()))
    profile = user.freelancer_profile
    if request.method == "GET":
        return jsonify([p.to_dict() for p in profile.portfolio_items])

    title = sanitize_text(request.form.get("title", ""))
    description = sanitize_text(request.form.get("description", ""))
    project_url = sanitize_text(request.form.get("project_url", ""))
    if not title:
        return jsonify({"error": "Title required"}), 400
    image_path = None
    if "file" in request.files:
        try:
            image_path = save_upload(request.files["file"], "portfolios", current_app.config["ALLOWED_IMAGE_EXTENSIONS"])
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
    item = PortfolioItem(profile_id=profile.id, title=title, description=description, image_path=image_path, project_url=project_url)
    db.session.add(item)
    db.session.commit()
    return jsonify(item.to_dict()), 201


@users_bp.route("/portfolio/<int:item_id>", methods=["DELETE"])
@jwt_required()
@role_required("student")
def delete_portfolio_item(item_id):
    user = User.query.get(int(get_jwt_identity()))
    profile = user.freelancer_profile
    if not profile:
        return jsonify({"error": "Profile not found"}), 404
        
    item = PortfolioItem.query.get_or_404(item_id)
    if item.profile_id != profile.id:
        return jsonify({"error": "Unauthorized"}), 403
        
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Portfolio item deleted successfully"})


@users_bp.route("/saved-freelancers", methods=["GET", "POST", "DELETE"])
@jwt_required()
@role_required("client")
def saved_freelancers():
    client_id = int(get_jwt_identity())
    if request.method == "GET":
        saved = SavedFreelancer.query.filter_by(client_id=client_id).all()
        result = []
        for s in saved:
            u = User.query.get(s.freelancer_id)
            if u and u.freelancer_profile:
                result.append(u.freelancer_profile.to_dict())
        return jsonify(result)
    if request.method == "POST":
        fid = request.get_json().get("freelancer_id")
        if SavedFreelancer.query.filter_by(client_id=client_id, freelancer_id=fid).first():
            return jsonify({"message": "Already saved"}), 200
        db.session.add(SavedFreelancer(client_id=client_id, freelancer_id=fid))
        db.session.commit()
        return jsonify({"message": "Freelancer saved"}), 201
    fid = request.args.get("freelancer_id", type=int)
    s = SavedFreelancer.query.filter_by(client_id=client_id, freelancer_id=fid).first()
    if s:
        db.session.delete(s)
        db.session.commit()
    return jsonify({"message": "Removed"})


@users_bp.route("/settings", methods=["PUT"])
@jwt_required()
def update_settings():
    user = User.query.get(int(get_jwt_identity()))
    data = request.get_json() or {}
    if "full_name" in data:
        user.full_name = sanitize_text(data["full_name"])
    if "campus" in data:
        user.campus = sanitize_text(data["campus"])
    if "email" in data:
        new_email = sanitize_text(data["email"]).lower()
        if User.query.filter(User.email == new_email, User.id != user.id).first():
            return jsonify({"error": "Email in use"}), 409
        user.email = new_email
    if "deposit_amount" in data:
        amount = float(data["deposit_amount"])
        if amount > 0:
            user.wallet_balance += amount
    db.session.commit()
    return jsonify({"message": "Settings updated", "user": user.to_dict(include_email=True)})


@users_bp.route("/profile/verify", methods=["POST"])
@jwt_required()
@role_required("student")
def verify_profile():
    user = User.query.get(int(get_jwt_identity()))
    profile = user.freelancer_profile
    if not profile:
        return jsonify({"error": "No freelancer profile found"}), 404
        
    data = request.get_json() or {}
    score = data.get("score", 0)
    topic = sanitize_text(data.get("topic", "General Skills"))
    
    if score >= 80:
        profile.is_verified = True
        
        # Grant XP and award verification achievement on pass!
        profile.xp = (profile.xp or 0) + 250
        if profile.xp >= 2000:
            profile.level = "Campus Expert"
        elif profile.xp >= 1000:
            profile.level = "Pro Freelancer"
        elif profile.xp >= 500:
            profile.level = "Skilled"
            
        achievement = Achievement(
            user_id=user.id,
            title="Verified Expert",
            description=f"Earned a passing grade of {score}% in the {topic} timed exam.",
            badge_icon="🛡️"
        )
        db.session.add(achievement)
        
        db.session.commit()
        create_notification(user.id, "🏅 Skill Verified!", f"Congratulations! You scored {score}% in the {topic} Quiz. Unlocked 'Verified Expert' and gained +250 XP!")
        log_activity(user.id, "skill_verification", f"Successfully verified skill in {topic} with score {score}%")
        return jsonify({"verified": True, "message": f"Congratulations! You are now a Verified Pro in {topic}."})
    else:
        return jsonify({"verified": False, "message": f"You scored {score}%. You need at least 80% to pass and verify this skill."})


# =========================================================================
# GAMIFICATION, LEADERBOARDS, XP, ACHIEVEMENTS, AND RESUME BUILDERS
# =========================================================================

from backend.models import Achievement

@users_bp.route("/leaderboard", methods=["GET"])
def get_leaderboard():
    profiles = FreelancerProfile.query.join(User).filter(
        User.is_active == True, User.is_banned == False
    ).options(joinedload(FreelancerProfile.user)).order_by(FreelancerProfile.xp.desc(), FreelancerProfile.rating_avg.desc()).limit(10).all()
    
    result = []
    for index, p in enumerate(profiles):
        ach_count = Achievement.query.filter_by(user_id=p.user_id).count()
        result.append({
            "rank": index + 1,
            "user_id": p.user_id,
            "full_name": p.user.full_name,
            "profile_picture": p.user.profile_picture,
            "level": p.level or "Rookie",
            "xp": p.xp or 0,
            "rating_avg": p.rating_avg,
            "achievements_count": ach_count,
            "is_verified": p.is_verified
        })
    return jsonify(result)


@users_bp.route("/achievements", methods=["GET"])
@jwt_required()
def get_achievements():
    user_id = int(get_jwt_identity())
    achieve = Achievement.query.filter_by(user_id=user_id).order_by(Achievement.unlocked_at.desc()).all()
    return jsonify([a.to_dict() for a in achieve])


@users_bp.route("/missions", methods=["GET"])
@jwt_required()
def get_missions():
    user_id = int(get_jwt_identity())
    profile = FreelancerProfile.query.filter_by(user_id=user_id).first()
    
    # Generate interactive missions based on profile status dynamically
    missions = [
        {
            "id": 1,
            "title": "Complete Skill Verification",
            "reward": "+250 XP",
            "status": "completed" if (profile and profile.is_verified) else "pending",
            "description": "Take a 60-second assessment quiz to unlock your golden Verified badge."
        },
        {
            "id": 2,
            "title": "Setup AI Bio summary",
            "reward": "+100 XP",
            "status": "completed" if (profile and profile.ai_summary) else "pending",
            "description": "Utilize our BART-based profile generator to draft a high-fidelity biography."
        },
        {
            "id": 3,
            "title": "Grow your Streak",
            "reward": "+50 XP",
            "status": "completed" if (profile and profile.streak_days > 5) else "pending",
            "description": "Check back for 5 consecutive days to establish campus momentum."
        }
    ]
    
    return jsonify({
        "streak_days": profile.streak_days if profile else 0,
        "missions": missions
    })


@users_bp.route("/resume-builder", methods=["GET"])
@jwt_required()
def get_resume():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    profile = user.freelancer_profile
    
    if not profile:
        return jsonify({"error": "No freelancer profile found"}), 404
        
    skills_list = [s.skill.name for s in profile.skills if s.skill]
    port_list = [{"title": p.title, "url": p.project_url or ""} for p in profile.portfolio_items]
    
    resume_markdown = f"""# {user.full_name.upper()}
*Campus: {user.campus or 'University Partner'} | Email: {user.email}*
*LinkedIn: {profile.linkedin_url or 'N/A'} | GitHub: {profile.github_url or 'N/A'}*

---

## 🚀 PROFESSIONAL SUMMARY
{profile.ai_summary or profile.bio or 'Experienced student growth ecosystem participant.'}

---

## 🛠️ CORE SKILLS & EXPERTISE
{', '.join(skills_list) if skills_list else 'Skill Verification Pending'}

---

## 💼 WORK & PROJECT EXPERIENCE
{profile.work_experience or 'No work experience added yet. Add it via your Profile tab!'}

---

## 🎓 EDUCATION & ACADEMICS
{profile.education or 'No education records added yet. Add it via your Profile tab!'}

---

## 📂 CREATIVE PORTFOLIO SHOWCASE
"""
    for index, p in enumerate(port_list):
        resume_markdown += f"{index+1}. **{p['title']}** (Link: {p['url'] or 'N/A'})\n"
        
    return jsonify({
        "resume_markdown": resume_markdown,
        "structural_data": {
            "name": user.full_name,
            "email": user.email,
            "headline": profile.headline,
            "skills": skills_list,
            "portfolio": port_list,
            "level": profile.level,
            "trust_score": profile.trust_score,
            "work_experience": profile.work_experience,
            "education": profile.education
        }
    })


# =========================================================================
# PUBLIC PORTFOLIO & FREELANCER SHAREABLE SLUG ROUTES
# =========================================================================

from backend.models import PublicProfile, PortfolioProject, ProfileReview

@users_bp.route("/public/<string:slug>", methods=["GET"])
def get_public_profile(slug):
    """Retrieve public profile lookup by custom slug (LinkedIn/Behance alternative)."""
    p = PublicProfile.query.filter_by(slug=slug).first()
    if not p:
        return jsonify({"error": "Public profile not found"}), 404
    
    # Increment portfolio views (analytical tracking)
    p.portfolio_views += 1
    db.session.commit()
    
    data = p.to_dict()
    
    # Also fetch actual project reviews for this freelancer
    from backend.models import Review
    project_reviews = Review.query.filter_by(reviewee_id=p.user_id).order_by(Review.created_at.desc()).all()
    
    # Merge project reviews with profile reviews
    for pr in project_reviews:
        data["reviews"].append({
            "id": pr.id,
            "reviewer_name": pr.reviewer.full_name if pr.reviewer else "Client",
            "rating": pr.rating,
            "comment": pr.comment,
            "created_at": pr.created_at.isoformat() if pr.created_at else None,
            "is_project_review": True
        })
        
    # Sort all reviews by date
    data["reviews"].sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    return jsonify(data)


@users_bp.route("/public-profile/me", methods=["GET", "PUT"])
@jwt_required()
def my_public_profile():
    """Retrieve or update the logged-in student's public profile custom details."""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    
    p = PublicProfile.query.filter_by(user_id=user_id).first()
    if not p:
        # Auto-create profile with slug from email or name
        slug = user.full_name.lower().replace(" ", "-")
        # Ensure unique slug
        idx = 1
        original_slug = slug
        while PublicProfile.query.filter_by(slug=slug).first():
            slug = f"{original_slug}-{idx}"
            idx += 1
            
        p = PublicProfile(
            user_id=user_id,
            slug=slug,
            bio=user.freelancer_profile.bio if user.freelancer_profile else "",
            github_url=user.freelancer_profile.github_url if user.freelancer_profile else "",
            linkedin_url=user.freelancer_profile.linkedin_url if user.freelancer_profile else ""
        )
        db.session.add(p)
        db.session.commit()
        
    if request.method == "GET":
        return jsonify(p.to_dict())
        
    # PUT: Update profile details
    data = request.get_json() or {}
    new_slug = sanitize_text(data.get("slug", p.slug)).strip().lower().replace(" ", "-")
    
    if not new_slug:
        return jsonify({"error": "Profile slug cannot be blank"}), 400
        
    # If slug changed, ensure unique
    if new_slug != p.slug:
        existing = PublicProfile.query.filter_by(slug=new_slug).first()
        if existing:
            return jsonify({"error": "Profile URL slug is already taken"}), 400
        p.slug = new_slug
        
    p.bio = sanitize_text(data.get("bio", p.bio))
    p.github_url = sanitize_text(data.get("github_url", p.github_url))
    p.linkedin_url = sanitize_text(data.get("linkedin_url", p.linkedin_url))
    db.session.commit()
    
    return jsonify({"message": "Public profile updated successfully", "profile": p.to_dict()})


@users_bp.route("/public-profile/me/projects", methods=["POST"])
@jwt_required()
def add_portfolio_project():
    """Add a creative portfolio showcase project to their public page."""
    user_id = int(get_jwt_identity())
    p = PublicProfile.query.filter_by(user_id=user_id).first_or_404()
    
    data = request.get_json() or {}
    title = sanitize_text(data.get("title", "")).strip()
    description = sanitize_text(data.get("description", "")).strip()
    image = sanitize_text(data.get("image", "/frontend/assets/default_proj.png")).strip()
    technologies = sanitize_text(data.get("technologies", "")).strip()
    live_demo_url = sanitize_text(data.get("live_demo_url", "")).strip()
    
    if not title:
        return jsonify({"error": "Project title is required"}), 400
        
    project = PortfolioProject(
        profile_id=p.id,
        title=title,
        description=description,
        image=image,
        technologies=technologies,
        live_demo_url=live_demo_url
    )
    db.session.add(project)
    db.session.commit()
    
    return jsonify(project.to_dict()), 201


@users_bp.route("/public-profile/me/projects/<int:proj_id>", methods=["DELETE"])
@jwt_required()
def remove_portfolio_project(proj_id):
    """Delete a creative portfolio showcase project."""
    user_id = int(get_jwt_identity())
    p = PublicProfile.query.filter_by(user_id=user_id).first_or_404()
    
    project = PortfolioProject.query.filter_by(id=proj_id, profile_id=p.id).first_or_404()
    db.session.delete(project)
    db.session.commit()
    
    return jsonify({"message": "Portfolio project removed successfully"})


@users_bp.route("/public/<string:slug>/reviews", methods=["POST"])
@jwt_required()
def submit_public_review(slug):
    """Allow logged-in clients to submit ratings and reviews to a student's public page."""
    user_id = int(get_jwt_identity())
    p = PublicProfile.query.filter_by(slug=slug).first_or_404()
    
    data = request.get_json() or {}
    rating = int(data.get("rating", 5))
    comment = sanitize_text(data.get("comment", "")).strip()
    
    if rating < 1 or rating > 5:
        return jsonify({"error": "Rating must be an integer between 1 and 5"}), 400
        
    review = ProfileReview(profile_id=p.id, reviewer_id=user_id, rating=rating, comment=comment)
    db.session.add(review)
    db.session.commit()
    
    # Optionally update freelancer avg ratings
    fp = FreelancerProfile.query.filter_by(user_id=p.user_id).first()
    if fp:
        all_reviews = ProfileReview.query.filter_by(profile_id=p.id).all()
        ratings = [r.rating for r in all_reviews]
        fp.rating_avg = sum(ratings) / len(ratings)
        fp.rating_count = len(ratings)
        db.session.commit()
        
    # Notify Receiver
    reviewer = User.query.get(user_id)
    create_notification(
        user_id=p.user_id,
        title="⭐ New Public Review!",
        message=f"{reviewer.full_name} left you a {rating}-star public review.",
        ntype="success"
    )
    
    return jsonify(review.to_dict()), 201
