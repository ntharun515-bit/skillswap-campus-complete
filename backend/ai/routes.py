"""AI features: summaries, skill suggestions, matching, chatbot (free/heuristic + optional HF)."""
import re
import requests
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.models import User, FreelancerProfile, Project, Skill, UserSkill
from backend.extensions import db
from backend.middleware.security import sanitize_text

ai_bp = Blueprint("ai", __name__, url_prefix="/api/ai")


def _heuristic_summary(profile, user):
    skills = ", ".join([s.skill.name for s in profile.skills[:5]]) if profile.skills else "various skills"
    return (
        f"{user.full_name} is a student freelancer at {user.campus or 'campus'} "
        f"specializing in {skills}. {profile.headline or ''} "
        f"Rated {profile.rating_avg:.1f}/5 from {profile.rating_count} reviews."
    ).strip()


def _skill_suggestions(existing_names):
    pool = [
        "Python", "JavaScript", "React", "UI Design", "Data Analysis",
        "Tutoring", "Essay Writing", "Video Editing", "Figma", "Java",
        "Machine Learning", "Excel", "Public Speaking", "Photography",
    ]
    return [s for s in pool if s.lower() not in [e.lower() for e in existing_names]][:6]


def _match_score(project, profile):
    score = 0
    req = (project.skills_required or "").lower()
    for us in profile.skills:
        if us.skill and us.skill.name.lower() in req:
            score += 30
    score += min(profile.rating_avg * 10, 50)
    if profile.availability == "available":
        score += 20
    return min(score, 100)


@ai_bp.route("/profile-summary", methods=["POST"])
@jwt_required()
def profile_summary():
    user = User.query.get(int(get_jwt_identity()))
    profile = user.freelancer_profile
    if not profile:
        return jsonify({"error": "No profile"}), 404
    summary = _heuristic_summary(profile, user)
    token = current_app.config.get("HUGGINGFACE_API_TOKEN")
    if token:
        try:
            resp = requests.post(
                "https://api-inference.huggingface.co/models/facebook/bart-large-cnn",
                headers={"Authorization": f"Bearer {token}"},
                json={"inputs": f"Summarize student freelancer profile: {summary}"},
                timeout=15,
            )
            if resp.status_code == 200 and isinstance(resp.json(), list):
                summary = resp.json()[0].get("summary_text", summary)
        except Exception as e:
            current_app.logger.warning(f"Failed to fetch HuggingFace summary: {e}")
    profile.ai_summary = summary
    db.session.commit()
    return jsonify({"summary": summary})


@ai_bp.route("/skill-suggestions", methods=["GET"])
@jwt_required()
def skill_suggestions():
    user = User.query.get(int(get_jwt_identity()))
    existing = [s.skill.name for s in user.freelancer_profile.skills] if user.freelancer_profile else []
    return jsonify({"suggestions": _skill_suggestions(existing)})


@ai_bp.route("/project-matches", methods=["GET"])
@jwt_required()
def project_matches():
    from sqlalchemy.orm import joinedload
    user = User.query.options(
        joinedload(User.freelancer_profile).joinedload(FreelancerProfile.skills).joinedload(UserSkill.skill)
    ).get(int(get_jwt_identity()))
    profile = user.freelancer_profile
    if not profile:
        return jsonify([])
    projects = Project.query.options(
        joinedload(Project.client),
        joinedload(Project.category),
        joinedload(Project.team),
        joinedload(Project.applications)
    ).filter_by(status="open").limit(20).all()
    matches = [{"project": p.to_dict(), "match_score": _match_score(p, profile)} for p in projects]
    matches.sort(key=lambda x: x["match_score"], reverse=True)
    return jsonify(matches[:10])


@ai_bp.route("/freelancer-recommendations/<int:project_id>", methods=["GET"])
@jwt_required()
def freelancer_recommendations(project_id):
    from sqlalchemy.orm import joinedload
    project = Project.query.get_or_404(project_id)
    profiles = FreelancerProfile.query.options(
        joinedload(FreelancerProfile.user),
        joinedload(FreelancerProfile.skills).joinedload(UserSkill.skill)
    ).limit(30).all()
    recs = [{"freelancer": p.to_dict(), "match_score": _match_score(project, p)} for p in profiles]
    recs.sort(key=lambda x: x["match_score"], reverse=True)
    return jsonify(recs[:10])


@ai_bp.route("/smart-search", methods=["GET"])
def smart_search():
    from sqlalchemy.orm import joinedload
    q = request.args.get("q", "").lower()
    if not q:
        return jsonify({"projects": [], "freelancers": []})
    projects = Project.query.options(
        joinedload(Project.client),
        joinedload(Project.category),
        joinedload(Project.team),
        joinedload(Project.applications)
    ).filter(
        (Project.title.ilike(f"%{q}%")) | (Project.description.ilike(f"%{q}%"))
    ).limit(10).all()
    profiles = FreelancerProfile.query.options(
        joinedload(FreelancerProfile.user),
        joinedload(FreelancerProfile.skills).joinedload(UserSkill.skill)
    ).join(User).filter(
        (User.full_name.ilike(f"%{q}%")) | (FreelancerProfile.headline.ilike(f"%{q}%"))
    ).limit(10).all()
    keywords = re.findall(r"\w+", q)
    return jsonify({
        "keywords": keywords,
        "projects": [p.to_dict() for p in projects],
        "freelancers": [f.to_dict() for f in profiles],
    })


@ai_bp.route("/chatbot", methods=["POST"])
def chatbot():
    data = request.get_json() or {}
    message = (data.get("message") or "").lower()
    
    # Check if there is an authenticated user via JWT
    from flask_jwt_extended import verify_jwt_in_request
    user_id = None
    try:
        verify_jwt_in_request(optional=True)
        user_identity = get_jwt_identity()
        if user_identity:
            user_id = int(user_identity)
    except Exception as e:
        current_app.logger.warning(f"Chatbot JWT parse skipped: {e}")

    # DB query helpers for dynamic replies
    if "open project" in message or "available project" in message or "jobs" in message or "how many project" in message:
        count = Project.query.filter_by(status="open").count()
        return jsonify({
            "reply": f"We currently have **{count} open projects** on campus! You can view and apply for them in the 'Browse Projects' section."
        })

    if "top freelancer" in message or "best freelancer" in message or "top rated" in message or "who is the best" in message or "tutor" in message:
        top_profiles = FreelancerProfile.query.order_by(FreelancerProfile.rating_avg.desc()).limit(3).all()
        names = []
        for p in top_profiles:
            if p.user:
                names.append(f"{p.user.full_name} ({p.headline or 'Student'}, Rated {p.rating_avg:.1f}⭐)")
        if names:
            return jsonify({
                "reply": f"Here are the top-rated student freelancers on campus right now:\n\n" + "\n".join([f"🔹 {n}" for n in names]) + "\n\nYou can chat with them directly or invite them to bid!"
            })
        return jsonify({"reply": "We have many talented students available! Browse the Freelancers page to find your perfect match."})

    if "how many user" in message or "number of user" in message or "popular" in message or "registered" in message:
        u_count = User.query.count()
        f_count = FreelancerProfile.query.count()
        return jsonify({
            "reply": f"SkillSwap is thriving! We currently have **{u_count} registered members**, including **{f_count} active student freelancers** ready to share skills."
        })

    if "balance" in message or "wallet" in message or "credits" in message or "my money" in message or "rupee" in message or "rupees" in message:
        if user_id:
            user = User.query.get(user_id)
            if user:
                return jsonify({
                    "reply": f"Hello {user.full_name}! Your current wallet balance is **₹{user.wallet_balance:.2f}**. Clients can use Rupees to fund projects, and students receive them upon milestone approvals!"
                })
        return jsonify({
            "reply": "Every client starts with **₹1000.00** in their wallet. When you hire a freelancer, the project budget is held in Escrow and safely released once the work is complete. Log in to check your active balance!"
        })

    # Standard guide replies
    replies = {
        "hello": "Hello! I'm your SkillSwap AI Campus Assistant. Ask me about open projects, top freelancers, platform statistics, or your wallet balance!",
        "hi": "Hi there! I'm SkillSwap AI. Ask me about open projects, top freelancers, platform statistics, or your wallet balance!",
        "project": "Clients can post projects with a set budget from their dashboard. Students can browse projects, submit applications, and pitch their rates.",
        "pay": "We use a secure virtual Escrow system! Project funds are locked when a student is hired and released directly to their wallet upon completion.",
        "verify": "Students can submit skill verification requests. Administrators review documentation or you can take a platform skill quiz!",
    }
    
    for key, reply in replies.items():
        if key in message:
            return jsonify({"reply": reply})
            
    return jsonify({
        "reply": "I can help you explore SkillSwap! Try asking me: \n\n"
                 "💡 *'How many open projects are there?'*\n"
                 "⭐ *'Who are the top freelancers?'*\n"
                 "💳 *'How does payment work?'*\n"
                 "📊 *'How many users are on the platform?'*"
    })


# =========================================================================
# AI SAFETY MODERATION, SKILL INTERVIEWS, AND CAREER ANALYTICS
# =========================================================================

from backend.models import AIInterview, Achievement

@ai_bp.route("/moderate", methods=["POST"])
@jwt_required()
def moderate_content():
    data = request.get_json() or {}
    text = (data.get("text") or "").lower()
    
    # Advanced Heuristic Scam, Spam, and Abuse scanner
    suspicious_patterns = [
        r"wire transfer", r"western union", r"send money", r"advance fee",
        r"free cash", r"make fast money", r"whatsapp me at", r"telegram me",
        r"double your money", r"buy bitcoin", r"invest cash"
    ]
    abuse_patterns = [
        r"idiot", r"jerk", r"stupid", r"fuck", r"shit", r"scam", r"fake"
    ]
    
    is_scam = any(re.search(pattern, text) for pattern in suspicious_patterns)
    is_abuse = any(re.search(pattern, text) for pattern in abuse_patterns)
    is_spam = len(text.split()) > 100 and len(set(text.split())) < len(text.split()) * 0.4
    
    flagged = is_scam or is_abuse or is_spam
    categories = []
    if is_scam: categories.append("scam/financial_fraud")
    if is_abuse: categories.append("abusive/toxic_language")
    if is_spam: categories.append("automated_spam/bulk_text")
    
    return jsonify({
        "flagged": flagged,
        "categories": categories,
        "confidence": 0.96 if flagged else 0.05,
        "recommendation": "Block/Filter content" if flagged else "Approve content"
    })


@ai_bp.route("/interviews/generate", methods=["POST"])
@jwt_required()
def generate_interview():
    data = request.get_json() or {}
    skill = sanitize_text(data.get("skill", "Python"))
    
    # Pre-compiled high-quality assessment blocks for campus skills
    assessments = {
        "Python": [
            {
                "id": 1,
                "question": "What is the output of: print(type(1 / 2)) in Python 3?",
                "options": ["<class 'int'>", "<class 'float'>", "<class 'double'>", "SyntaxError"],
                "answer": "<class 'float'>"
            },
            {
                "id": 2,
                "question": "Which of the following data structures is mutable?",
                "options": ["Tuple", "List", "String", "Integer"],
                "answer": "List"
            },
            {
                "id": 3,
                "question": "What does the 'self' keyword represent in Python class methods?",
                "options": ["A reference to the class itself", "A reference to the current instance of the class", "A global scope variable", "A reserved keyword for inheritance"],
                "answer": "A reference to the current instance of the class"
            },
            {
                "id": 4,
                "question": "What is the primary difference between a list and a generator in Python?",
                "options": ["List is mutable, generator is immutable", "Generators produce items on the fly using lazy evaluation, saving memory compared to list lists", "List can contain only integers, generator can contain any type", "Generators are executing faster in single-thread operations"],
                "answer": "Generators produce items on the fly using lazy evaluation, saving memory compared to list lists"
            },
            {
                "id": 5,
                "question": "Which of the following creates a deep copy of an object in Python?",
                "options": ["copy.copy(obj)", "copy.deepcopy(obj)", "obj.copy()", "dict(obj)"],
                "answer": "copy.deepcopy(obj)"
            }
        ],
        "React": [
            {
                "id": 1,
                "question": "What is the primary purpose of the 'useEffect' Hook in React?",
                "options": ["To update the local state variable", "To perform side effects in functional components", "To bind inline styles", "To accelerate rendering speed"],
                "answer": "To perform side effects in functional components"
            },
            {
                "id": 2,
                "question": "Which command triggers a state rerender in React?",
                "options": ["this.forceRerender()", "Calling a state setter function", "Mutating a ref object", "Adding a global class list"],
                "answer": "Calling a state setter function"
            },
            {
                "id": 3,
                "question": "In React, how do you pass data from a parent component down to a child component?",
                "options": ["Using browser LocalStorage", "Using parameters inside the fetch API", "Passing attributes as 'props' down to the child component", "Exporting a shared context provider"],
                "answer": "Passing attributes as 'props' down to the child component"
            },
            {
                "id": 4,
                "question": "What is a major advantage of the React Virtual DOM?",
                "options": ["It communicates directly with cloud databases", "It keeps a lightweight copy of the UI and only updates modified nodes in the real DOM, optimizing render performance", "It replaces the CSS styles sheets", "It runs calculations in a background WebWorker thread"],
                "answer": "It keeps a lightweight copy of the UI and only updates modified nodes in the real DOM, optimizing render performance"
            },
            {
                "id": 5,
                "question": "What hook should you use to preserve values across renders without triggering a rerender?",
                "options": ["useState", "useRef", "useMemo", "useContext"],
                "answer": "useRef"
            }
        ],
        "Design": [
            {
                "id": 1,
                "question": "What is the primary difference between UX and UI design?",
                "options": ["UX deals with visual aesthetics, UI deals with ease of use", "UX deals with overall usability and user journey, UI deals with interface components", "There is no difference between them", "UX only applies to physical products"],
                "answer": "UX deals with overall usability and user journey, UI deals with interface components"
            },
            {
                "id": 2,
                "question": "What design strategy describes styling elements with glass-like transparency, frosted blur, and thin border glows?",
                "options": ["Neumorphism", "Flat Design 2.0", "Glassmorphism", "Skeuomorphism"],
                "answer": "Glassmorphism"
            },
            {
                "id": 3,
                "question": "Which color scheme leverages HSL calculations to guarantee a premium dark-first brand aesthetics?",
                "options": ["Monochromatic light tones", "Obsidian black base paired with cyber purple neon borders", "Plain primary red, blue, and yellow", "High-frequency saturated warm colors"],
                "answer": "Obsidian black base paired with cyber purple neon borders"
            },
            {
                "id": 4,
                "question": "What design token describes the spacing between characters inside text headings?",
                "options": ["Line Height", "Font Weight", "Letter Spacing (Tracking)", "Horizontal Alignment"],
                "answer": "Letter Spacing (Tracking)"
            },
            {
                "id": 5,
                "question": "What is the key purpose of micro-animations in a premium SaaS interface?",
                "options": ["To distract the user during slow API loads", "To provide quick, delightful visual feedback on interactions like hover or click", "To decrease the bundle size of CSS files", "To replace traditional nav-bar menus"],
                "answer": "To provide quick, delightful visual feedback on interactions like hover or click"
            }
        ],
        "Database Security": [
            {
                "id": 1,
                "question": "Which defense is most effective against SQL Injection (SQLi) vulnerabilities?",
                "options": ["Using plain string concatenation for queries", "Sanitizing input by removing quotes", "Using parameterized queries and prepared statements (ORM)", "Obfuscating table names"],
                "answer": "Using parameterized queries and prepared statements (ORM)"
            },
            {
                "id": 2,
                "question": "What is the primary goal of Cross-Site Scripting (XSS) prevention?",
                "options": ["Preventing unauthorized database reads", "Preventing hackers from injecting malicious scripts into client browsers", "Limiting client API rate quotas", "Hiding backend Flask debug pins"],
                "answer": "Preventing hackers from injecting malicious scripts into client browsers"
            },
            {
                "id": 3,
                "question": "Which HTTP header protects websites against clickjacking attacks?",
                "options": ["Content-Type", "Authorization", "X-Frame-Options", "User-Agent"],
                "answer": "X-Frame-Options"
            },
            {
                "id": 4,
                "question": "What cryptographically secure standard is used to maintain stateful user sessions in single-page apps safely?",
                "options": ["Plain base64 strings", "JSON Web Tokens (JWT)", "In-memory variables", "Static cookie strings"],
                "answer": "JSON Web Tokens (JWT)"
            },
            {
                "id": 5,
                "question": "What database authorization practice ensures developers only have permissions necessary to perform their roles?",
                "options": ["Standard Superuser credentials sharing", "Role-Based Access Control (RBAC) and Principle of Least Privilege", "Disabling SQL database logs", "Disallowing foreign keys structures"],
                "answer": "Role-Based Access Control (RBAC) and Principle of Least Privilege"
            }
        ],
        "Machine Learning": [
            {
                "id": 1,
                "question": "What represents the main objective of Supervised Machine Learning?",
                "options": ["To let models learn patterns without any labels", "To train algorithms on paired input-output training datasets to predict labels for new data", "To optimize CSS styling rules automatically", "To encrypt user password models"],
                "answer": "To train algorithms on paired input-output training datasets to predict labels for new data"
            },
            {
                "id": 2,
                "question": "In regression models, what does an 'overfitting' state mean?",
                "options": ["The model is too simple to capture patterns", "The model matches the training dataset extremely closely but performs poorly on unseen validation data", "The database is out of index variables", "The weights converge immediately to zero"],
                "answer": "The model matches the training dataset extremely closely but performs poorly on unseen validation data"
            },
            {
                "id": 3,
                "question": "Which Python library is most widely used for model building, training, and evaluations in classic Machine Learning?",
                "options": ["Pandas", "Scikit-Learn", "Matplotlib", "SocketIO"],
                "answer": "Scikit-Learn"
            },
            {
                "id": 4,
                "question": "What metrics are commonly used to measure regression model errors?",
                "options": ["Precision and Recall", "Mean Squared Error (MSE) and Root Mean Squared Error (RMSE)", "Accuracy and F1 Score", "Confusion Matrix coordinates"],
                "answer": "Mean Squared Error (MSE) and Root Mean Squared Error (RMSE)"
            },
            {
                "id": 5,
                "question": "What is natural language processing (NLP) primary usage in a professional student marketplace?",
                "options": ["To design flowcharts diagrams", "To parse and moderate portfolios bios or detect scams", "To compute wallet ledger totals", "To scale real-time socket connections"],
                "answer": "To parse and moderate portfolios bios or detect scams"
            }
        ]
    }
    
    questions = assessments.get(skill, [
        {
            "id": 1,
            "question": f"Which parameter is critical to successfully deliver standard {skill} deliverables?",
            "options": ["High response speed", "Quality assurance reviews", "Budget limitations", "All of the above"],
            "answer": "All of the above"
        }
    ])
    
    return jsonify({
        "skill": skill,
        "questions": questions
    })


@ai_bp.route("/interviews/evaluate", methods=["POST"])
@jwt_required()
def evaluate_interview():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    data = request.get_json() or {}
    
    skill = sanitize_text(data.get("skill", "Python"))
    score = int(data.get("score", 0))
    total = int(data.get("total", 3))
    
    percentage = int((score / total) * 100) if total > 0 else 0
    passed = percentage >= 80
    
    # Generate comprehensive evaluation report text
    report = (
        f"AI Career Assessment Report for {user.full_name}\n"
        f"Skill Assessed: {skill}\n"
        f"Final Score: {score}/{total} ({percentage}%)\n\n"
        f"Evaluation Summary:\n"
        f"The candidate demonstrated strong knowledge in {skill}. "
        f"{'Passed: Verified credentials unlocked on the platform.' if passed else 'Failed: Score fell below the 80% verification threshold.'}"
    )
    
    interview = AIInterview(
        user_id=user_id,
        skill_name=skill,
        score=percentage,
        evaluation_report=report
    )
    db.session.add(interview)
    
    # Unlock verification rewards if passed!
    if passed:
        profile = FreelancerProfile.query.filter_by(user_id=user_id).first()
        if profile:
            profile.is_verified = True
            profile.xp = (profile.xp or 0) + 250
            if profile.xp >= 2000:
                profile.level = "Campus Expert"
            elif profile.xp >= 1000:
                profile.level = "Pro Freelancer"
                
            db.session.add(Achievement(
                user_id=user_id,
                title=f"{skill} Pro",
                description=f"Scored {percentage}% in the timed {skill} AI assessment.",
                badge_icon="🎓"
            ))
            
    db.session.commit()
    
    return jsonify({
        "passed": passed,
        "score_percentage": percentage,
        "evaluation_report": report
    })


@ai_bp.route("/interviews/history", methods=["GET"])
@jwt_required()
def interview_history():
    user_id = int(get_jwt_identity())
    history = AIInterview.query.filter_by(user_id=user_id).order_by(AIInterview.created_at.desc()).all()
    return jsonify([h.to_dict() for h in history])


@ai_bp.route("/analytics", methods=["GET"])
@jwt_required()
def career_analytics():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    profile = user.freelancer_profile
    
    if user.role.name == "student":
        # Freelancer Analytics
        predicted_earnings = [100, 150, 220, 310, 450] # Month projections
        skill_trends = [
            {"skill": "React", "demand": "increased", "growth": "18%"},
            {"skill": "Python", "demand": "stable", "growth": "12%"},
            {"skill": "UI/UX", "demand": "increased", "growth": "25%"}
        ]
        
        return jsonify({
            "role": "student",
            "predicted_earnings": predicted_earnings,
            "skill_growth_trends": skill_trends,
            "ai_success_prediction": 94.0 if (profile and profile.is_verified) else 78.0,
            "best_category": "Web Development",
            "activity_heatmap": [8, 12, 15, 20, 18, 22, 25] # Days count
        })
    else:
        # Client Analytics
        return jsonify({
            "role": "client",
            "hiring_patterns": "Heavy mid-semester spike in Tutoring & Web design",
            "budget_insights": "Average project spends are currently averaging 120.00 Cr",
            "freelancer_performance": 96.5, # Avg hired student rating
            "project_success_rate": 100.0 # Completed vs Total
        })


@ai_bp.route("/roadmap", methods=["GET"])
@jwt_required()
def get_career_roadmap():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    profile = user.freelancer_profile
    role = request.args.get("role", "Full Stack Engineer")
    
    # Grab student's verified skills
    verified_skills = []
    if profile:
        verified_skills = [s.skill.name for s in profile.skills]
        
    # Predefined roadmaps
    roadmaps = {
        "Full Stack Engineer": {
            "steps": ["Frontend Developer", "React UI Specialist", "Full Stack Cloud Engineer"],
            "skills": ["HTML", "JavaScript", "React", "Python"],
            "description": "Master both frontend visual frameworks and secure, parameterized backend databases.",
            "step_details": {
                "Frontend Developer": {
                    "concepts": ["HTML5 Semantic Tags", "CSS Grid & Flexbox Layouts", "DOM Manipulation"],
                    "resources": [
                        {"name": "MDN HTML Basics", "url": "https://developer.mozilla.org/en-US/docs/Learn/HTML"},
                        {"name": "CSS Tricks Guide to Flexbox", "url": "https://css-tricks.com/snippets/css/a-guide-to-flexbox/"}
                    ]
                },
                "React UI Specialist": {
                    "concepts": ["Functional Components", "React Hooks (useState, useEffect)", "Context API for State"],
                    "resources": [
                        {"name": "React Dev Reference", "url": "https://react.dev/"},
                        {"name": "FreeCodeCamp React Course", "url": "https://www.freecodecamp.org/learn/front-end-development-libraries/"}
                    ]
                },
                "Full Stack Cloud Engineer": {
                    "concepts": ["RESTful Routing Architectures", "SQLAlchemy Parameterized Queries", "JWT Shield Security"],
                    "resources": [
                        {"name": "Flask-SocketIO Documentation", "url": "https://flask-socketio.readthedocs.io/"},
                        {"name": "SQLAlchemy Basics Tutorial", "url": "https://docs.sqlalchemy.org/"}
                    ]
                }
            }
        },
        "React Specialist": {
            "steps": ["UI Designer", "Frontend Developer", "React Specialist"],
            "skills": ["HTML", "JavaScript", "React", "Design"],
            "description": "Create premium, glassmorphic layout components and high-performance WebSocket listeners.",
            "step_details": {
                "UI Designer": {
                    "concepts": ["Figma Vector Outlines", "Cyber Glassmorphism Rules", "HSL Harmony Palette Design"],
                    "resources": [
                        {"name": "Refactoring UI Principles", "url": "https://www.refactoringui.com/"},
                        {"name": "Glassmorphism Generator tool", "url": "https://cssglass.io/"}
                    ]
                },
                "Frontend Developer": {
                    "concepts": ["CSS Variables Hierarchy", "Responsive Viewports Queries", "Async JS Fetching"],
                    "resources": [
                        {"name": "JavaScript.info Guide", "url": "https://javascript.info/"},
                        {"name": "Google Fonts API Guide", "url": "https://developers.google.com/fonts"}
                    ]
                },
                "React Specialist": {
                    "concepts": ["Dynamic DOM Rendering", "State Management Models", "Websocket Emitters integration"],
                    "resources": [
                        {"name": "Socket.IO JS Tutorial", "url": "https://socket.io/docs/v4/tutorial/introduction"},
                        {"name": "Modern React Hooks cheatsheet", "url": "https://react.dev/reference/react"}
                    ]
                }
            }
        },
        "Data Scientist": {
            "steps": ["Data Analyst", "Machine Learning Specialist", "Data Scientist"],
            "skills": ["Python", "Excel", "Data Analysis", "Machine Learning"],
            "description": "Leverage natural language processing filters and predictive monthly projections.",
            "step_details": {
                "Data Analyst": {
                    "concepts": ["Excel Advanced Pivots", "Data Wrangling with Pandas", "Matplotlib Charts drawing"],
                    "resources": [
                        {"name": "Pandas Getting Started", "url": "https://pandas.pydata.org/docs/getting_started/index.html"},
                        {"name": "Kaggle Data Analytics Course", "url": "https://www.kaggle.com/learn"}
                    ]
                },
                "Machine Learning Specialist": {
                    "concepts": ["Linear Regression concepts", "Scikit-Learn model training", "Feature Weight Adjustments"],
                    "resources": [
                        {"name": "Scikit-Learn Tutorials", "url": "https://scikit-learn.org/stable/tutorial/"},
                        {"name": "Machine Learning Crash Course", "url": "https://developers.google.com/machine-learning/crash-course"}
                    ]
                },
                "Data Scientist": {
                    "concepts": ["NLP Text Scanners", "BART Bio Generator scripts", "Predictive Projection algorithms"],
                    "resources": [
                        {"name": "Hugging Face Models Hub", "url": "https://huggingface.co/models"},
                        {"name": "PyTorch Getting Started Guide", "url": "https://pytorch.org/get-started/locally/"}
                    ]
                }
            }
        }
    }
    
    selected = roadmaps.get(role, roadmaps["Full Stack Engineer"])
    
    # Calculate Gaps
    gap_analysis = []
    for s in selected["skills"]:
        has_skill = s.lower() in [vs.lower() for vs in verified_skills]
        gap_analysis.append({
            "skill": s,
            "verified": has_skill,
            "status": "Verified ✅" if has_skill else "Required quiz ⚠️"
        })
        
    # Grab open projects matching the target skills
    from sqlalchemy.orm import joinedload
    matching_projects = []
    open_projects = Project.query.options(
        joinedload(Project.client),
        joinedload(Project.category),
        joinedload(Project.team),
        joinedload(Project.applications)
    ).filter_by(status="open").all()
    for p in open_projects:
        req = (p.skills_required or "").lower()
        if any(s.lower() in req for s in selected["skills"]):
            matching_projects.append(p.to_dict())
            
    return jsonify({
        "role": role,
        "steps": selected["steps"],
        "description": selected["description"],
        "gaps": gap_analysis,
        "step_details": selected.get("step_details", {}),
        "recommendations": matching_projects[:3]
    })


@ai_bp.route("/ideas-generator", methods=["POST"])
@jwt_required()
def generate_project_idea():
    data = request.get_json() or {}
    skills = data.get("skills", ["Python"])
    
    # Custom project ideas based on combinations of skills
    ideas_db = {
        "python": {
            "title": "⚡ Real-Time Campus Traffic Analytics Server",
            "problem": "University shuttle routes and lab occupancy rates are currently untracked, leading to high waiting times.",
            "stack": "Python / Flask-SocketIO / SQLite",
            "milestones": [
                "Set up Flask backend with parameterized room tracking",
                "Integrate real-time SocketIO broadcasters emitting occupancy metrics",
                "Create a simple SQLite ledger logging passenger timestamps securely"
            ]
        },
        "react": {
            "title": "🎨 Glassmorphic Booking Portal for Campus Labs",
            "problem": "Students face booking conflicts when reserving premium team study rooms and VR equipments.",
            "stack": "React / Space Grotesk / CSS glassmorphic variables",
            "milestones": [
                "Design a clean, 3-column booking calendar using interactive states",
                "Implement a dynamic roadmap checklist verifying reservation rules",
                "Connect real-time notifications alerting team members on seat releases"
            ]
        },
        "design": {
            "title": "🧭 High-Fidelity UI System for Student Incubators",
            "problem": "Early-stage student startup proposals look simple and unprofessional, failing to attract seed investors.",
            "stack": "Figma / CSS Variable Tokens / Harmony HSL Palettes",
            "milestones": [
                "Conduct full typography hierarchy audits using geometric fonts",
                "Establish fluid responsive grid rules matching tablet and mobile layouts",
                "Build dynamic floating dashboard components with smooth micro-animations"
            ]
        }
    }
    
    # Find match based on selected skills
    chosen_idea = None
    for s in skills:
        key = s.lower()
        if key in ideas_db:
            chosen_idea = ideas_db[key]
            break
            
    if not chosen_idea:
        # Default fallback
        chosen_idea = {
            "title": "🚀 Custom Campus SaaS Integration",
            "problem": "Manual spreadsheets are used to record peer verification and timed assessments on campus.",
            "stack": "Flask-SocketIO / React UI / Parameters Security",
            "milestones": [
                "Establish high-contrast dashboard grids mapping user progress indicators",
                "Program secure API gateways validating credentials and badges automatically",
                "Deploy dynamic line sparklines rendering weekly engagement indexes"
            ]
        }
        
    return jsonify(chosen_idea)


@ai_bp.route("/resume-analyzer", methods=["POST"])
@jwt_required()
def analyze_resume():
    """AI-powered Resume and ATS Compatibility Scanner."""
    user = User.query.get(int(get_jwt_identity()))
    profile = user.freelancer_profile
    
    data = request.get_json() or {}
    resume_text = sanitize_text(data.get("resume_text", ""))
    target_role = sanitize_text(data.get("target_role", "Full Stack Engineer"))
    
    # If no resume text is passed, auto-compile it from their profile!
    if not resume_text and profile:
        skills_list = [s.skill.name for s in profile.skills if s.skill]
        resume_text = f"""
        Name: {user.full_name}
        Headline: {profile.headline or ""}
        Bio: {profile.bio or ""}
        Skills: {", ".join(skills_list)}
        Experience: {profile.work_experience or ""}
        Education: {profile.education or ""}
        """
        
    text_lower = resume_text.lower()
    
    # 1. ATS Score Calculation (Out of 100)
    score = 45 # Base score
    
    # Check for contact info / professional URLs
    if "linkedin.com" in text_lower or (profile and profile.linkedin_url):
        score += 10
    if "github.com" in text_lower or (profile and profile.github_url):
        score += 10
    if "@" in text_lower:
        score += 5
        
    # Check for standard ATS sections
    sections = ["experience", "education", "skills", "summary"]
    for sec in sections:
        if sec in text_lower:
            score += 5
            
    # Check for core industry standard keywords matching target roles
    role_keywords = {
        "Full Stack Engineer": ["api", "database", "git", "rest", "frontend", "backend", "deployment"],
        "React Specialist": ["javascript", "css", "state", "hooks", "component", "dom", "npm"],
        "Data Scientist": ["python", "pandas", "numpy", "statistics", "model", "sql", "analysis"]
    }
    
    matched_keywords = []
    missing_keywords = []
    target_keywords = role_keywords.get(target_role, role_keywords["Full Stack Engineer"])
    
    for kw in target_keywords:
        if kw in text_lower:
            score += 3
            matched_keywords.append(kw)
        else:
            missing_keywords.append(kw)
            
    # Bound the score between 0 and 100
    ats_score = min(score, 100)
    
    # 2. Grammar & Tone Analysis
    grammar_issues = []
    # Check for use of passive / weak verbs
    passive_indicators = ["responsible for", "duties included", "helped in", "assisted with", "managed by"]
    for pi in passive_indicators:
        if pi in text_lower:
            grammar_issues.append(f"Replace passive phrase '{pi}' with a strong active verb (e.g., 'Designed', 'Spearheaded', 'Engineered').")
            
    if not grammar_issues:
        grammar_issues.append("Excellent grammar and tone! The choice of words feels professional, clear, and direct.")
        grammar_score = 98
    else:
        grammar_score = max(100 - (len(grammar_issues) * 15), 65)
        
    # 3. Missing Skills Detection
    # Suggest advanced technical skills to gain complete edge based on role
    role_skills_map = {
        "Full Stack Engineer": ["Docker", "Redis", "Nginx", "Kubernetes", "TailwindCSS", "PostgreSQL"],
        "React Specialist": ["TypeScript", "Redux Toolkit", "Next.js", "Websocket", "Jest", "Sass"],
        "Data Scientist": ["PyTorch", "Scikit-Learn", "TensorFlow", "Jupyter", "Docker", "GCP"]
    }
    
    suggested_skills = role_skills_map.get(target_role, role_skills_map["Full Stack Engineer"])
    detected_missing_skills = []
    
    # If student already has the skill, skip it
    existing_skills = [s.skill.name.lower() for s in profile.skills if s.skill] if profile else []
    for s in suggested_skills:
        if s.lower() not in existing_skills and s.lower() not in text_lower:
            detected_missing_skills.append(s)
            
    # 4. Actionable Improvement Suggestions
    suggestions = [
        "Quantify your accomplishments: Add concrete numbers, percentages, or savings (e.g., 'Improved load times by 40%' or 'Managed 5 study resources').",
        "Improve structure: Keep descriptions under standard bullet points instead of dense paragraphs to ensure high machine readability.",
        "Ensure standard fonts: Use classic fonts like Inter, Sora, or Helvetica, and avoid graphic text elements."
    ]
    
    if len(detected_missing_skills) > 0:
        suggestions.append(f"Consider verifying the missing skill '{detected_missing_skills[0]}' on the platform to boost profile rankings.")
        
    return jsonify({
        "ats_score": ats_score,
        "grammar_score": grammar_score,
        "grammar_analysis": grammar_issues,
        "missing_skills": detected_missing_skills,
        "improvement_suggestions": suggestions,
        "matched_keywords": matched_keywords
    })


@ai_bp.route("/project-estimate", methods=["POST"])
def project_estimate():
    data = request.get_json() or {}
    category_id = data.get("category_id")
    skills_required = data.get("skills_required", "")
    complexity = data.get("complexity", "medium").lower()
    
    # Baseline calculations
    base_budgets = {
        "dev-tech": 300,
        "design-creative": 200,
        "content-writing": 100,
        "marketing": 150,
        "academic-services": 80,
        "ai-automation": 400,
        "media-production": 250,
        "data-analytics": 300
    }
    
    category_slug = "dev-tech"
    if category_id:
        from backend.models import Category
        category = Category.query.get(category_id)
        if category:
            category_slug = category.slug
            
    base_budget = base_budgets.get(category_slug, 150)
    
    # Complexity factors
    if complexity == "low":
        mult = 0.6
        dur = "3-7 days"
    elif complexity == "high":
        mult = 2.2
        dur = "1-3 months"
    else:
        mult = 1.0
        dur = "2-4 weeks"
        
    # Skill count factor
    skill_list = [s.strip() for s in skills_required.split(",") if s.strip()] if isinstance(skills_required, str) else (skills_required or [])
    skill_count = len(skill_list)
    skill_mult = 1.0 + (min(skill_count, 8) * 0.1)
    
    suggested_budget = round(base_budget * mult * skill_mult, 2)
    
    # Generate dynamic skills list based on category
    recommendations = {
        "dev-tech": ["Python", "Flask", "React", "Docker", "Git", "PostgreSQL"],
        "design-creative": ["Figma", "UI Design", "Adobe Illustrator", "Motion Graphics"],
        "content-writing": ["SEO", "Copywriting", "Creative Writing", "Technical Writing"],
        "marketing": ["Google Analytics", "SEO", "Social Media", "Content Strategy"],
        "academic-services": ["Calculus", "Essay Editing", "Research", "Tutoring"],
        "ai-automation": ["Prompt Engineering", "OpenAI API", "Python", "Machine Learning"],
        "media-production": ["Video Editing", "Premiere Pro", "After Effects", "Color Grading"],
        "data-analytics": ["SQL", "Pandas", "Tableau", "Excel", "Data Visualization"]
    }
    recommended = recommendations.get(category_slug, ["Communication", "Project Management"])
    
    return jsonify({
        "suggested_budget": suggested_budget,
        "suggested_duration": dur,
        "recommended_skills": recommended,
        "confidence_score": 0.85
    })


@ai_bp.route("/generate-proposal", methods=["POST"])
@jwt_required()
def generate_proposal():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    profile = user.freelancer_profile if user else None
    
    data = request.get_json() or {}
    project_id = data.get("project_id")
    tone = data.get("tone", "professional").lower()
    focus = data.get("focus", "experience").lower()
    
    project = Project.query.get_or_404(project_id)
    
    # Determine the intro based on tone
    if tone == "friendly":
        intro = f"Hey there! I saw your post for '{project.title}' and got super excited."
        closing = "Would love to jump on a quick chat and brainstorm together! Cheers,"
    elif tone == "confident":
        intro = f"Hi! I am writing to express my strong interest in '{project.title}'. Based on my proven track record, I am confident I can deliver exceptional results."
        closing = "Let's schedule a brief call to discuss how I can add immediate value to this project. Best regards,"
    else: # professional
        intro = f"Dear Client,\n\nI am writing to submit my proposal for your project '{project.title}'. With my technical background and relevant skill set, I am well-suited for this opportunity."
        closing = "Thank you for considering my proposal. I look forward to the possibility of collaborating with you.\n\nSincerely,"
        
    # Focus area customization
    if focus == "speed":
        focus_paragraph = "I understand that fast delivery is key for this task. I have a highly efficient workflow and can dedicate immediate hours to ensure high-quality, rapid turnaround."
    elif focus == "low cost":
        focus_paragraph = f"I am offering competitive pricing for this milestone. My goal is to build long-term campus relationships, so I'm happy to provide maximum value within your {project.budget} budget."
    else: # experience
        user_skills = ", ".join([s.skill.name for s in profile.skills[:3]]) if profile and profile.skills else "Software Engineering"
        focus_paragraph = f"I specialize in {user_skills} and have tackled similar challenges. I always focus on clean, scalable code and robust system architectures."
        
    # Heuristic template creation
    proposal = (
        f"{intro}\n\n"
        f"Your project description states: '{project.description[:120]}...'. This matches my technical toolkit perfectly. "
        f"{focus_paragraph}\n\n"
        f"I have verified skills in {project.skills_required or 'the requested fields'} and would love to bring this expertise to your project. "
        f"{closing}\n"
        f"{user.full_name if user else 'Student Developer'}"
    )
    
    # Optional Hugging Face integration
    token = current_app.config.get("HUGGINGFACE_API_TOKEN")
    if token:
        try:
            prompt = f"Write a professional freelance cover letter for a project titled: {project.title}. My name is {user.full_name}. Tone: {tone}. Focus: {focus}."
            resp = requests.post(
                "https://api-inference.huggingface.co/models/gpt2",
                headers={"Authorization": f"Bearer {token}"},
                json={"inputs": prompt, "parameters": {"max_new_tokens": 150}},
                timeout=10
            )
            if resp.status_code == 200 and isinstance(resp.json(), list):
                generated_text = resp.json()[0].get("generated_text", "")
                if generated_text and len(generated_text) > len(prompt):
                    proposal = generated_text[len(prompt):].strip()
        except Exception as e:
            current_app.logger.warning(f"Failed to generate HuggingFace cover letter: {e}")
            
    return jsonify({
        "proposal": proposal,
        "tone": tone,
        "focus": focus
    })


@ai_bp.route("/portfolio-score", methods=["GET"])
@jwt_required()
def portfolio_score():
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    profile = user.freelancer_profile if user else None
    
    if not profile:
        return jsonify({"error": "No freelancer profile found."}), 404
        
    score = 30 # baseline score
    
    # 1. Headline (max 10)
    headline_len = len(profile.headline or "")
    if headline_len > 15:
        score += 10
    elif headline_len > 5:
        score += 5
        
    # 2. Bio (max 15)
    bio_len = len(profile.bio or "")
    if bio_len > 100:
        score += 15
    elif bio_len > 30:
        score += 8
        
    # 3. Skills count (max 20)
    skills_count = len(profile.skills)
    score += min(skills_count * 4, 20)
    
    # 4. Verified skills (max 15)
    verified_skills = sum(1 for s in profile.skills if s.is_verified)
    score += min(verified_skills * 5, 15)
    
    # 5. Average reviews rating (max 20)
    rating = profile.rating_avg or 0.0
    score += min(round(rating * 4, 1), 20)
    
    # 6. Portfolio items count (max 20)
    items_count = len(profile.portfolio_items)
    score += min(items_count * 5, 20)
    
    final_score = min(score, 100)
    
    # Break down the feedback
    positives = []
    improvements = []
    
    if headline_len > 15:
        positives.append("Compelling professional headline matches industry roles.")
    else:
        improvements.append("Refine your professional headline to be more descriptive (e.g. 'Full Stack Engineer specializing in React').")
        
    if bio_len > 100:
        positives.append("Rich profile biography describes your goals and background comprehensively.")
    else:
        improvements.append("Expand your bio with key projects, academic background, and core technologies.")
        
    if skills_count >= 5:
        positives.append("Broad skill dictionary loaded onto your active profile.")
    else:
        improvements.append("Add at least 5 technical or interpersonal skills to highlight your toolbox.")
        
    if verified_skills > 0:
        positives.append(f"Credibility bolstered by {verified_skills} verified skill badges.")
    else:
        improvements.append("Verify your top skills by taking interactive campus AI quizzes.")
        
    if items_count >= 3:
        positives.append(f"Impressive catalog of {items_count} case studies in your portfolio showcase.")
    else:
        improvements.append("Add more past project screenshots or github links to your portfolio showcase.")
        
    if not positives:
        positives.append("Ecosystem profile initialized successfully.")
        
    return jsonify({
        "score": final_score,
        "ratings_avg": rating,
        "portfolio_count": items_count,
        "skills_count": skills_count,
        "positives": positives,
        "improvements": improvements
    })


@ai_bp.route("/detect-fraud", methods=["GET"])
@jwt_required()
def detect_fraud():
    # Allow querying a specific user_id (useful for admin), otherwise default to current logged in user
    user_id_param = request.args.get("user_id", type=int)
    if user_id_param:
        target_user = User.query.get(user_id_param)
    else:
        target_user = User.query.get(int(get_jwt_identity()))
        
    if not target_user:
        return jsonify({"error": "User not found"}), 404
        
    profile = target_user.freelancer_profile
    if not profile:
        return jsonify({
            "is_scam": False,
            "risk_score": 5,
            "reasons": ["No active student freelancer profile associated with this account."]
        })
        
    text = f"{profile.headline or ''} {profile.bio or ''}".lower()
    
    risk_score = 10 # baseline risk
    reasons = []
    
    # 1. Look for suspicious contact patterns
    scam_keywords = {
        "whatsapp": 25,
        "telegram": 25,
        "wire transfer": 30,
        "gift card": 30,
        "send money": 20,
        "crypto": 15,
        "bitcoin": 20,
        "guaranteed income": 25,
        "make money fast": 30,
        "no experience needed": 15,
        "pay upfront": 25,
        "off-platform": 20
    }
    
    for kw, penalty in scam_keywords.items():
        if kw in text:
            risk_score += penalty
            reasons.append(f"Suspicious transaction lure keyword detected: '{kw}' (+{penalty}% risk)")
            
    # 2. Text duplication/spam checks
    words = text.split()
    if len(words) > 30:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.5:
            risk_score += 20
            reasons.append("High text repetition indicates automated spam spinning (+20% risk)")
            
    # 3. Quick sanity check on email
    if "temp" in target_user.email.lower() or "throwaway" in target_user.email.lower():
        risk_score += 35
        reasons.append("Temporary / throwaway email provider pattern (+35% risk)")
        
    # Bound risk score between 0 and 100
    final_risk = min(risk_score, 100)
    is_scam = final_risk >= 50
    
    if not reasons:
        reasons.append("No suspicious text, contact, or email patterns detected. Profile is safe.")
        
    return jsonify({
        "user_id": target_user.id,
        "full_name": target_user.full_name,
        "email": target_user.email,
        "is_scam": is_scam,
        "risk_score": final_risk,
        "reasons": reasons
    })

