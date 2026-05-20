# 🚀 SkillSwap: AI-Powered Student Professional Growth Ecosystem

**SkillSwap** is an AI-powered student professional growth ecosystem designed to help students gain real-world experience, collaborate on projects, monetize skills, and build verified professional identities through intelligent workflows and modern collaboration systems.

The platform is designed to look, feel, and function like premium tech products such as **Linear**, **Notion**, **Vercel**, and **Stripe**—using a highly polished, responsive **obsidian dark glass design** and high-contrast **Space Grotesk** typography.

---

## 🧭 Signature Highlight: AI Career Roadmap Engine
The platform's standout feature is the **AI Career Roadmap Engine**. This adaptive intelligent system analyzes student skills, completed projects, certifications, and activity patterns to generate personalized professional growth pathways:

```
[Frontend Developer] ──> [React UI Specialist] ──> [Full Stack Cloud Engineer]
```

### Core Capabilities:
- **Interactive Flowcharts:** Watch visual flowchart nodes connect and adjust instantly as you toggle your target pathway dropdown in real-time.
- **Skill Gaps Analysis:** Automatically scans the student's verified skills and provides direct, dynamic verification triggers (`⚡ Verify Skill`).
- **One-Click Exams Launch:** If a required skill is missing, clicking its check button instantly scrolls and launches the timed technical quiz for that topic.
- **Dynamic Project Recommendations:** Recommends active, open campus campaigns matching your roadmap milestones.

---

## 🧠 Core System Modules

### 🖥️ 1. Notion-Style Collaborative Workdesks
Unified workspaces shared in real-time between students (`student/workspace.html`) and clients (`client/workspace.html`):
- **Project Lifecycle Timeline:** An animated stepper tracking contract progression states (`Open` ➔ `In Progress` ➔ `Submitted` ➔ `Completed`).
- **Linear-Style Kanban Board:** A professional 4-column drag-and-drop taskboard (`To Do`, `In Progress`, `Review`, `Done`) that synchronizes task cards across teammates via WebSockets.
- **Secure Escrow Balance Release:** Locked virtual credit pools automatically funded by clients and released to the student's wallet upon milestone reviews.
- **Workspace Activity Log:** Chronological, immutable audit log of status updates, deliverables uploads, and settlements.

### 🎓 2. Skill Verification Hub
A timed testing room where students take 60-second technical assessments (Python, React, or Design). Scoring $\ge 80\%$ unlocks the **Verification Achievement System**, rewarding students with `+250 XP` and pinning a permanent **Verified Pro** badge onto their profiles.

### 📂 3. Smart Resume Generator
Compile your active portfolio projects, client review ratings, trust reliability scores, and verified skill badges into a beautifully structured **Markdown CV**. Copy it directly to your clipboard or download it as an `.md` file instantly!

### 🔄 4. Event-Driven Realtime Architecture
Powered by **asynchronous Eventlet workers** and **Flask-SocketIO** for non-blocking direct messages chat rooms, instant notification banners, and live task board updates.

---

## 🔐 Security & Reliability Infrastructure
SkillSwap implements production-grade security architecture to safeguard data and assets:
- **JWT Authentication:** Cryptographically signed tokens managing secure user sessions.
- **Role-Based Access Control (RBAC):** Strict navigation and route shielding between Student, Client, and Admin roles.
- **SQLi Prevention:** Parameterized SQL queries using SQLAlchemy ORM.
- **XSS & CSRF Mitigation:** Automated input sanitization and secure API routing filters.
- **IP Rate Limiting:** Limits request frequencies using Flask-Limiter.
- **System Health Monitor:** Dedicated diagnostic endpoints (`/api/health`) tracking database and socket connectivity.

---

## 🛠️ Tech Stack & Design Aesthetics
- **Core backend:** Python, Flask, Flask-SocketIO, Eventlet, SQLAlchemy ORM.
- **Database Engine:** Relational architecture backing SQLite (default) and MySQL.
- **Frontend Architecture:** Vanilla HTML, CSS Variable Design Tokens, JS dynamic components.
- **Design Tokens:** Cyber obsidian black palette (`#030712`), frosted glassmorphism overlays, and neon border glows.
- **Typography:** **Space Grotesk** (tech-forward geometric headings) and **Plus Jakarta Sans** (legible body texts).

---

## 🚀 Quick Start (Easiest — SQLite Local Runner)

To start the local development server in your environment, execute the following commands in PowerShell:

```powershell
# 1. Navigate to directory
cd skillswap-campus-complete

# 2. Set up virtual environment
python -m venv .venv
& .venv\Scripts\activate

# 3. Install core dependencies
pip install -r requirements.txt

# 4. Copy environment configuration
copy .env.example .env

# 5. Initialize the relational database & seed content
python database\init_db.py

# 6. Boot the Werkzeug SocketIO development server
python run.py
```

Open **`http://localhost:5000`** in your browser.

### 🔑 Verified Demo Credentials

| Role | Username / Email | Password | Key Access Area |
| :--- | :--- | :--- | :--- |
| **Student** | `alex@campus.edu` | `Demo123!` | Career & AI Hub, Timed Exams, Shared Workspace |
| **Client** | `jordan@campus.edu` | `Demo123!` | Escrow Release, Milestone Progress, Shared Workspace |
| **Admin** | `admin@skillswap.edu` | `Admin123!` | Mediation disputes desk, verification logs |

---

## 📁 Project Structure

```
├── backend/            # Flask API, Socket.IO routes, and database models
│   ├── api/            # Base API handlers (wallets, disputes, users)
│   ├── ai/             # AI roadmap engines, timed quizzes, and CV compilers
│   └── models.py       # Modular relational database tables
├── frontend/           # Modern Glassmorphic Client & Student interfaces
│   ├── css/            # Style variables, global styles, and sidebar styling
│   ├── js/             # API helpers, auth state, and dynamic components
│   └── pages/          # Student, Client, and Admin HTML layouts
├── database/           # Relational schemas, inits, and seeder scripts
├── docs/               # Technical specs, testing docs, and API guides
└── run.py              # SocketIO server launcher
```
