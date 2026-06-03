# 🧪 SkillSwap: Step-by-Step Feature Validation & Testing Guide

This guide outlines how to manually verify and test all the active modules in your SkillSwap campus workspace. Since the server is running locally on [http://127.0.0.1:5001](http://127.0.0.1:5001), you can perform these checks using standard browser tabs.

---

## 🔑 Demo Access Credentials

| Role | Username / Email | Password | Primary Desk |
| :--- | :--- | :--- | :--- |
| **Student** | `alex@campus.edu` | `Demo123!` | Timed Assessments, Team Workspace, Career Path |
| **Client** | `jordan@campus.edu` | `Demo123!` | Escrow Funding & releases, Post job postings |
| **Admin** | `admin@skillswap.edu` | `Admin123!` | Disputes arbitration logs, verification checks |

---

## 🏁 Step 1: Authentication & Navigation Flow
1. Open your browser and go to [http://127.0.0.1:5001](http://127.0.0.1:5001).
2. Go to the **Login** page and sign in using `alex@campus.edu` (Student credentials).
3. Confirm that you are automatically redirected to `/frontend/pages/student/dashboard.html` (Student Dashboard).
4. Click **Sign Out** in the sidebar.
5. Log back in using `jordan@campus.edu` (Client credentials) and confirm redirection to the Client Dashboard.

---

## 🚀 Step 2: Timed Assessment & Verification Hub (Student Role)
1. Log in as **Alex** (Student: `alex@campus.edu`).
2. Navigate to **Career & AI Hub** via the sidebar.
3. Choose a pathway like **React Specialist** or **Data Scientist**. Watch the interactive flowchart update in real time.
4. Locate the **Required quiz ⚠️** warning next to skills like **React** or **Python**.
5. Click the quiz button to launch a **timed 60-second technical assessment**.
6. Answer the multiple-choice questions:
   - Scoring **$\ge 80\%$** unlocks verification.
7. Return to the dashboard and verify:
   - Your account is awarded **`+250 XP`**.
   - A **Verified Pro** badge checkmark appears next to your name.
   - The badge is pinned to your achievements list.

---

## 📝 Step 3: Smart Resume Markdown CV Generator (Student Role)
1. While logged in as **Alex** (Student), click **Portfolio** or **Resume Generator** in the sidebar.
2. Click **Generate/Compile Resume**.
3. The engine parses completed projects, review ratings, trust scores, and badges.
4. Verify that a complete **Markdown CV** is displayed.
5. Click **Download Resume** to save it as an `.md` file, or copy it directly to your clipboard.

---

## 🖥️ Step 4: Shared Workdesk & Escrow Cycle (Two-User Collaboration)
To test this, open **two separate browser sessions** (e.g., one normal tab and one Incognito tab):

### Session A: Client (Jordan - `jordan@campus.edu`)
1. Go to **Post Project** and create a campaign with a budget of `400.00 Cr` (e.g., *"Design Glassmorphic UI System"*).
2. Save it and verify it displays under open listings.

### Session B: Student (Alex - `alex@campus.edu`)
1. Go to **Browse Projects** and find Jordan's listing.
2. Click **Apply**, write a quick cover letter, and submit a proposed bid of `400.00 Cr`.

### Session A: Client
1. Navigate to **Applicants** or **Manage Projects**.
2. Locate Alex's bid and click **Accept Bid / Hire**.
3. Go to the **Shared Workdesk** or **Payments** page and fund the project escrow.
4. Verify that Jordan's wallet balance decrements by `400.00 Cr` and the escrow ledger locks the funds.

### Session B: Student
1. Go to **Shared Workdesk** and select the hired project.
2. The animated project timeline will transition to **In Progress**.
3. Create a card on the **Kanban Board** and drag/move it columns. Verify that the updates sync instantly using WebSockets.
4. Use the **Project Chat** panel to send a message. Verify that Jordan receives a real-time notification alert instantly.
5. Fill out the handoff fields and click **Submit Deliverables**. The project timeline shifts to **Submitted**.

### Session A: Client
1. Go to the **Shared Workdesk** and verify that Alex's submissions and files are visible.
2. Check the logs under the activity audit trail.
3. Click **Release Escrow Payment** to approve the handoff.
4. Verify that Alex's available wallet balance increases by `400.00 Cr`.

---

## 🤖 Step 5: Heuristic AI Chatbot
1. Locate the floating **AI Assistant** icon in the bottom-right corner of any page.
2. Click the chat bubble.
3. Ask the assistant any of the suggested questions:
   - *"How many open projects are there?"*
   - *"Who are the top freelancers?"*
   - *"Check my credit balance"* (make sure you are logged in).
4. Verify the bot dynamically queries the database and gives immediate, customized statistics.

---

## 📊 Step 6: Student Dashboard Details & Checkpoints
1. Log in as **Alex** (Student: `alex@campus.edu`).
2. On the **Dashboard**, check the following widgets:
   - **XP Progress Bar**: Displays current XP (e.g., `250 XP`) and level (`Rookie` or `Pro Freelancer` depending on assessment passes).
   - **Earnings Flow Graph**: An interactive SVG line graph showing cumulative earnings. Hover over the nodes to see tooltip summaries.
   - **Active Milestone Checkpoints**: If you have an active hired project, you will see checklist items with checkboxes.
     - Toggle the checkboxes.
     - Verify that the card shifts state instantly and a success toast alerts you of database updates.
   - **My Active Proposals (Bids)**: Shows your pending, accepted, or declined bids.
   - **AI Recommended Projects**: Renders campus projects that match your profile skills with match percentage ratings.
   - **Campus Leaderboard**: Shows top users ranked by XP, tier, and ratings.

---

## 💼 Step 7: Client Dashboard Controls & Project Pipeline
1. Log in as **Jordan** (Client: `jordan@campus.edu`).
2. On the **Client Dashboard**, verify these panels:
   - **Project Pipeline**: A beautiful horizontal layout bar showing proportions of campaigns in `Open` (Green), `In Progress` (Yellow), `In Review` (Blue), and `Done` (White) phases.
   - **Interactive Wallet Controls**:
     - Input an amount (e.g., `250`) and click **Add Funds** or click the preset buttons (`+100 Cr`, `+500 Cr`, `+1000 Cr`).
     - Verify that your wallet balance is updated instantly on the page and sidebar!
   - **Active Campaigns**: Table showing active contracts. If a project is `Submitted` for review, a blue **Review** action button will appear. Clicking it launches the workdesk directly.
   - **Dispute Alerts Banner**: If there is an active dispute, a red warning alert is shown at the top of the dashboard.

---

## 🛡️ Step 8: Admin Operational Control & AI Security Scam Scanner
1. Log in as **Admin** (`admin@skillswap.edu` / `Admin123!`).
2. On the **System Operations Dashboard**, check:
   - **System Stats**: Total accounts, projects posted, flags raised, and cumulative platform fee calculations (5%).
   - **Escrow Dispute Mediation Center**: Active disputes are listed here.
     - Try clicking **Refund Client** or **Release to Freelancer** to resolve a dispute.
     - Confirm the action prompts and check that the dispute status updates to `resolved`.
   - **Live Operational Broadcast Terminal**: Displays a running log of real-time actions.
     - Open a different browser and register a new user or log in.
     - Watch the terminal dynamically prepend new event rows in real time via Socket.IO broadcasts!
   - **AI Security Scam Scanner**:
     - Input a student or client user ID (e.g., `1` or `2`) and click **Scan**.
     - Verify the AI returns a **verdict status** (🟢 SAFE / 🚨 HIGH RISK), threat index percentage bar, and diagnostic risk triggers.

