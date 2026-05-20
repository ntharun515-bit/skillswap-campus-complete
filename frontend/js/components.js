/** Reusable UI components */
function renderNavbar(active = "") {
  const user = getUser();
  return `
    <nav class="navbar">
      <div class="container">
        <a href="/frontend/pages/public/index.html" class="logo">SkillSwap</a>
        <button class="nav-toggle" onclick="document.querySelector('.nav-links').classList.toggle('open')">☰</button>
        <ul class="nav-links">
          <li><a href="/frontend/pages/public/index.html" class="${active === "home" ? "active" : ""}">Home</a></li>
          <li><a href="/frontend/pages/public/projects.html" class="${active === "projects" ? "active" : ""}">Projects</a></li>
          <li><a href="/frontend/pages/public/freelancers.html" class="${active === "freelancers" ? "active" : ""}">Freelancers</a></li>
          <li><a href="/frontend/pages/public/about.html">About</a></li>
          <li><a href="/frontend/pages/public/faq.html">FAQ</a></li>
          ${user
            ? `<li><a href="#" onclick="redirectByRole('${user.role}');return false;">Dashboard</a></li>
               <li><button class="btn btn-ghost btn-sm" onclick="logout()">Logout</button></li>`
            : `<li><a href="/frontend/pages/public/login.html">Login</a></li>
               <li><a href="/frontend/pages/public/register.html" class="btn btn-primary btn-sm">Sign Up</a></li>`}
          <li><button class="theme-toggle btn-ghost btn-sm" onclick="toggleTheme()">🌙</button></li>
        </ul>
      </div>
    </nav>`;
}

function renderFooter() {
  return `
    <footer class="footer" style="border-top:1px solid var(--border);padding:3rem 0 2rem;margin-top:4rem">
      <div class="container">
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:2rem;margin-bottom:2rem">
          <div>
            <h4 style="font-size:1.1rem;font-weight:800;margin-bottom:1rem;font-family:var(--font-heading)">SkillSwap <span style="font-size:0.65rem;color:var(--accent);border:1px solid var(--accent);padding:0.1rem 0.35rem;border-radius:999px;margin-left:0.25rem">SaaS</span></h4>
            <p style="font-size:0.85rem;color:var(--text-secondary);line-height:1.6;max-width:260px">The next-generation student talent marketplace. Post projects, hire verified peers, and transact with secure campus credit escrow.</p>
          </div>
          <div>
            <h4 style="font-size:0.85rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:1rem;color:var(--text-secondary)">Platform</h4>
            <ul style="list-style:none;padding:0;display:flex;flex-direction:column;gap:0.5rem;font-size:0.88rem">
              <li><a href="/frontend/pages/public/projects.html" style="color:var(--text-secondary);text-decoration:none">Browse Projects</a></li>
              <li><a href="/frontend/pages/public/freelancers.html" style="color:var(--text-secondary);text-decoration:none">Find Freelancers</a></li>
              <li><a href="/frontend/pages/public/register.html" style="color:var(--text-secondary);text-decoration:none">Create Account</a></li>
              <li><a href="/frontend/pages/public/login.html" style="color:var(--text-secondary);text-decoration:none">Sign In</a></li>
            </ul>
          </div>
          <div>
            <h4 style="font-size:0.85rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:1rem;color:var(--text-secondary)">Resources</h4>
            <ul style="list-style:none;padding:0;display:flex;flex-direction:column;gap:0.5rem;font-size:0.88rem">
              <li><a href="/frontend/pages/public/about.html" style="color:var(--text-secondary);text-decoration:none">About Us</a></li>
              <li><a href="/frontend/pages/public/faq.html" style="color:var(--text-secondary);text-decoration:none">FAQ & Help</a></li>
              <li><a href="/frontend/pages/public/contact.html" style="color:var(--text-secondary);text-decoration:none">Contact Support</a></li>
            </ul>
          </div>
          <div>
            <h4 style="font-size:0.85rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;margin-bottom:1rem;color:var(--text-secondary)">Trust & Safety</h4>
            <ul style="list-style:none;padding:0;display:flex;flex-direction:column;gap:0.5rem;font-size:0.88rem">
              <li style="color:var(--text-secondary)">🛡️ Smart Escrow Protection</li>
              <li style="color:var(--text-secondary)">🔐 JWT Secure Authentication</li>
              <li style="color:var(--text-secondary)">⚖️ Admin Dispute Mediation</li>
              <li style="color:var(--text-secondary)">📜 Full Activity Audit Logs</li>
            </ul>
          </div>
        </div>
        <div style="border-top:1px solid var(--border);padding-top:1.5rem;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem">
          <p style="font-size:0.82rem;color:var(--text-secondary)">&copy; ${new Date().getFullYear()} SkillSwap. Built for students, by students.</p>
          <div style="display:flex;gap:1.25rem;font-size:0.82rem">
            <a href="/frontend/pages/public/faq.html" style="color:var(--text-secondary);text-decoration:none">Help</a>
            <a href="/frontend/pages/public/contact.html" style="color:var(--text-secondary);text-decoration:none">Support</a>
            <a href="/frontend/pages/public/about.html" style="color:var(--text-secondary);text-decoration:none">About</a>
          </div>
        </div>
      </div>
    </footer>`;
}

function renderSidebar(role, active) {
  const user = getUser();
  const menus = {
    student: [
      { href: "dashboard.html", label: "Dashboard", icon: "📊" },
      { href: "career.html", label: "Career & AI Hub", icon: "🚀" },
      { href: "workspace.html", label: "Shared Workdesk", icon: "🖥️" },
      { href: "projects.html", label: "Browse Projects", icon: "💼" },
      { href: "applications.html", label: "Applications", icon: "📝" },
      { href: "messages.html", label: "Messages", icon: "💬" },
      { href: "notifications.html", label: "Notifications", icon: "🔔" },
      { href: "earnings.html", label: "Earnings", icon: "💰" },
      { href: "portfolio.html", label: "Portfolio", icon: "🎨" },
      { href: "reviews.html", label: "Reviews", icon: "⭐" },
      { href: "settings.html", label: "Settings", icon: "⚙️" },
    ],
    client: [
      { href: "dashboard.html", label: "Dashboard", icon: "📊" },
      { href: "workspace.html", label: "Shared Workdesk", icon: "🖥️" },
      { href: "disputes.html", label: "Disputes Desk", icon: "⚖️" },
      { href: "post-project.html", label: "Post Project", icon: "➕" },
      { href: "manage-projects.html", label: "Manage Projects", icon: "📁" },
      { href: "applicants.html", label: "Applicants", icon: "👥" },
      { href: "messages.html", label: "Messages", icon: "💬" },
      { href: "payments.html", label: "Payments", icon: "💳" },
      { href: "analytics.html", label: "Analytics", icon: "📈" },
      { href: "saved.html", label: "Saved Freelancers", icon: "❤️" },
      { href: "settings.html", label: "Settings", icon: "⚙️" },
    ],
    admin: [
      { href: "dashboard.html", label: "Dashboard", icon: "📊" },
      { href: "users.html", label: "Users", icon: "👤" },
      { href: "reports.html", label: "Reports", icon: "🚩" },
      { href: "analytics.html", label: "Analytics", icon: "📈" },
      { href: "categories.html", label: "Categories", icon: "🏷️" },
      { href: "revenue.html", label: "Revenue", icon: "💵" },
      { href: "verification.html", label: "Verification", icon: "✅" },
    ],
  };
  const items = menus[role] || [];
  const base = `/frontend/pages/${role}/`;

  // Query live balance to keep sidebar assets absolutely in sync
  setTimeout(() => {
    API.get('/auth/me').then(u => {
      const el = document.getElementById('sidebar-wallet-value');
      if (el) el.textContent = u.wallet_balance.toFixed(2) + ' Cr';
      localStorage.setItem(CONFIG.USER_KEY, JSON.stringify(u));
    }).catch(() => {});
  }, 100);

  const initialBalance = user ? (user.wallet_balance || 0).toFixed(2) : '0.00';
  const roleLabel = role === 'student' ? '🎓 Campus Talent' : '💼 Platform Client';

  return `
    <aside class="sidebar" id="sidebar">
      <div class="sidebar-logo">
        SkillSwap <span style="font-size:0.6rem;font-weight:700;color:var(--accent);border:1px solid var(--accent);padding:0.15rem 0.4rem;border-radius:999px;margin-left:0.5rem;text-transform:uppercase;letter-spacing:0.05em">SaaS</span>
      </div>

      <!-- Profile Capsule -->
      <div style="padding:0.75rem;margin-bottom:1rem;border-bottom:1px solid var(--border)">
        <div style="display:flex;align-items:center;gap:0.65rem">
          <div style="width:36px;height:36px;border-radius:50%;background:var(--accent-glow);border:2px solid var(--accent);display:flex;align-items:center;justify-content:center;font-weight:800;color:var(--accent);font-size:0.9rem;font-family:var(--font-heading);flex-shrink:0">
            ${user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
          </div>
          <div style="min-width:0">
            <div style="font-size:0.85rem;font-weight:700;color:var(--text-primary);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${user?.full_name || 'Campus Member'}</div>
            <div style="font-size:0.7rem;color:var(--text-secondary)">${roleLabel}</div>
          </div>
        </div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:0.75rem;padding-top:0.6rem;border-top:1px solid var(--border)">
          <span style="font-size:0.72rem;color:var(--text-secondary);font-weight:600">Wallet</span>
          <span id="sidebar-wallet-value" style="font-family:var(--font-heading);font-weight:800;color:var(--success);font-size:0.88rem">${initialBalance} Cr</span>
        </div>
      </div>

      <ul class="sidebar-nav">
        ${items.map((m) => `
          <li><a href="${base}${m.href}" class="${active === m.href.replace(".html", "") ? "active" : ""}">
            <span>${m.icon}</span> ${m.label}
          </a></li>`).join("")}
      </ul>
      
      <div class="sidebar-footer" style="margin-top:auto;padding-top:1rem;border-top:1px solid var(--border)">
        <button class="btn btn-ghost" style="width:100%;font-size:0.85rem;padding:0.5rem" onclick="logout()">🚪 Sign Out</button>
      </div>
    </aside>`;
}

function renderDashboardHeader(title) {
  const user = getUser();
  return `
    <header class="dashboard-header" style="display:flex;justify-content:space-between;align-items:center;padding:0.75rem 2rem;border-bottom:1px solid var(--border);background:var(--bg-glass);backdrop-filter:blur(var(--blur));-webkit-backdrop-filter:blur(var(--blur))">
      <div style="display:flex;align-items:center;gap:0.6rem">
        <button class="btn btn-ghost btn-sm" onclick="document.getElementById('sidebar').classList.toggle('open')" style="padding:0.35rem 0.5rem">☰</button>
        <h1 style="font-size:1.1rem;font-weight:800;letter-spacing:-0.02em;margin:0;font-family:var(--font-heading)">${title}</h1>
      </div>
      <div style="display:flex;align-items:center;gap:1rem;margin-left:auto;position:relative">
        
        <!-- Premium Bell Notification Widget -->
        <div class="bell-widget-container" style="position:relative">
          <button class="btn btn-ghost" id="header-bell-btn" onclick="toggleNotificationDrawer(event)" style="padding:0.35rem 0.5rem;font-size:1.2rem;position:relative;background:none;border:none;cursor:pointer">
            🔔
            <span id="bell-unread-badge" style="display:none;position:absolute;top:-2px;right:-2px;background:var(--danger);color:#fff;border-radius:50%;width:16px;height:16px;font-size:0.65rem;font-weight:800;align-items:center;justify-content:center">0</span>
          </button>
          
          <!-- Obsidian Glass Notification Dropdown Drawer -->
          <div class="glass notification-drawer" id="header-notification-drawer" style="display:none;position:absolute;top:42px;right:0;width:320px;max-height:400px;background:var(--bg-glass);backdrop-filter:blur(var(--blur));border:1px solid var(--border);border-radius:var(--radius-lg);box-shadow:0 8px 32px rgba(0,0,0,0.5);z-index:9999;flex-direction:column;overflow:hidden">
            <div style="display:flex;justify-content:space-between;align-items:center;padding:0.75rem 1rem;border-bottom:1px solid var(--border);background:rgba(255,255,255,0.02)">
              <h3 style="font-size:0.9rem;margin:0;font-family:var(--font-heading);font-weight:800;color:var(--text-primary)">Live Alerts</h3>
              <button class="btn btn-ghost btn-sm" style="font-size:0.75rem;padding:0.15rem 0.4rem;border:none;background:none;color:var(--accent);cursor:pointer" onclick="markAllNotificationsRead(event)">Clear all</button>
            </div>
            <div id="drawer-notifications-list" style="overflow-y:auto;max-height:280px;display:flex;flex-direction:column">
              <div style="padding:2rem;text-align:center;color:var(--text-secondary);font-size:0.85rem">No notifications found</div>
            </div>
            <div style="border-top:1px solid var(--border);background:rgba(255,255,255,0.01);text-align:center;padding:0.5rem">
              <a href="/frontend/pages/student/notifications.html" style="font-size:0.78rem;color:var(--accent);text-decoration:none;font-weight:700">View All Notifications →</a>
            </div>
          </div>
        </div>

        <span style="font-size:0.82rem;font-weight:600;color:var(--text-secondary)">${user?.full_name || ""}</span>
        <button class="theme-toggle btn btn-ghost" onclick="toggleTheme()" style="padding:0.35rem 0.5rem;font-size:1rem;border-radius:var(--radius-sm)">🌙</button>
      </div>
    </header>`;
}

function showSkeleton(container, count = 3) {
  container.innerHTML = Array(count).fill('<div class="glass card skeleton" style="height:120px"></div>').join("");
}

function formatDate(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString();
}

function formatMoney(n) {
  return "$" + Number(n || 0).toFixed(2);
}

// Interactive Premium Floating AI Chatbot Widget
function initAIChatbot() {
  if (document.getElementById("ai-chatbot-widget")) return;

  const container = document.createElement("div");
  container.id = "ai-chatbot-widget";
  container.innerHTML = `
    <div class="ai-chatbot-bubble" id="chatbot-bubble" title="Ask AI Assistant">🤖</div>
    <div class="ai-chatbot-panel glass" id="chatbot-panel">
      <div class="ai-chatbot-header">
        <h3>🤖 SkillSwap AI Assistant</h3>
        <button class="ai-chatbot-close" id="chatbot-close">✕</button>
      </div>
      <div class="ai-chatbot-body" id="chatbot-body">
        <div class="ai-chatbot-msg bot">
          Hi! I'm your **SkillSwap AI Assistant**. Ask me about campus projects, top freelancers, platform statistics, or your virtual credit balance!
        </div>
        <div class="ai-chatbot-chips">
          <span class="ai-chatbot-chip" data-msg="How many open projects are there?">💼 Open Projects</span>
          <span class="ai-chatbot-chip" data-msg="Who are the top freelancers?">⭐ Top Freelancers</span>
          <span class="ai-chatbot-chip" data-msg="How does payment work?">💳 Payment Flow</span>
          <span class="ai-chatbot-chip" data-msg="Check my credit balance">💰 My Balance</span>
        </div>
      </div>
      <div class="ai-chatbot-footer">
        <input type="text" class="ai-chatbot-input" id="chatbot-input" placeholder="Ask something..." autocomplete="off">
        <button class="ai-chatbot-send-btn" id="chatbot-send">Send</button>
      </div>
    </div>
  `;

  document.body.appendChild(container);

  const bubble = document.getElementById("chatbot-bubble");
  const panel = document.getElementById("chatbot-panel");
  const closeBtn = document.getElementById("chatbot-close");
  const sendBtn = document.getElementById("chatbot-send");
  const input = document.getElementById("chatbot-input");
  const body = document.getElementById("chatbot-body");

  // Toggle Panel
  bubble.onclick = () => {
    panel.classList.toggle("open");
    if (panel.classList.contains("open")) {
      input.focus();
      body.scrollTop = body.scrollHeight;
    }
  };

  // Close Panel
  closeBtn.onclick = () => {
    panel.classList.remove("open");
  };

  // Click Suggestion Chips
  container.querySelectorAll(".ai-chatbot-chip").forEach((chip) => {
    chip.onclick = () => {
      submitMessage(chip.dataset.msg);
    };
  });

  // Handle Input submit
  input.onkeydown = (e) => {
    if (e.key === "Enter") {
      submitMessage(input.value);
    }
  };

  sendBtn.onclick = () => {
    submitMessage(input.value);
  };

  function appendMessage(text, sender) {
    // Basic formatting for **bold** text and newlines
    let formattedText = text
      .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
      .replace(/\*(.*?)\*/g, "<em>$1</em>")
      .replace(/\n/g, "<br>");
      
    const msgDiv = document.createElement("div");
    msgDiv.className = `ai-chatbot-msg ${sender}`;
    msgDiv.innerHTML = formattedText;
    body.appendChild(msgDiv);
    body.scrollTop = body.scrollHeight;
    return msgDiv;
  }

  async function submitMessage(msg) {
    if (!msg || !msg.trim()) return;
    input.value = "";
    
    // User message
    appendMessage(msg, "user");

    // Add loading typing indicator
    const typingIndicator = appendMessage("Thinking...", "bot");

    try {
      const headers = { "Content-Type": "application/json" };
      const token = localStorage.getItem("skillswap_access_token");
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const res = await fetch(`${window.location.origin}/api/ai/chatbot`, {
        method: "POST",
        headers,
        body: JSON.stringify({ message: msg }),
      });

      const data = await res.json();
      body.removeChild(typingIndicator);
      
      appendMessage(data.reply || "I'm having trouble connecting to the servers right now.", "bot");
    } catch (err) {
      body.removeChild(typingIndicator);
      appendMessage("Unable to contact AI server. Make sure the backend server is running.", "bot");
    }
  }
}

// Auto-boot the AI Chatbot once DOM and assets are fully operational
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    initAIChatbot();
    initNotificationSystem();
  });
} else {
  initAIChatbot();
  initNotificationSystem();
}


// =========================================================================
// 🔔 REAL-TIME NOTIFICATION SYSTEM CONTROLLER
// =========================================================================

function toggleNotificationDrawer(event) {
  if (event) event.stopPropagation();
  const drawer = document.getElementById("header-notification-drawer");
  if (!drawer) return;
  const isHidden = drawer.style.display === "none";
  drawer.style.display = isHidden ? "flex" : "none";
  if (isHidden) {
    fetchHeaderNotifications();
  }
}

// Close drawer on clicking outside
document.addEventListener("click", () => {
  const drawer = document.getElementById("header-notification-drawer");
  if (drawer) drawer.style.display = "none";
});

function initNotificationSystem() {
  // Sync starting alerts
  fetchHeaderNotifications();

  // Connect to Socket.IO real-time channel
  setTimeout(() => {
    const socketInstance = (typeof initSocket === "function") ? initSocket() : null;
    if (socketInstance) {
      socketInstance.on("notification", (data) => {
        // Dynamic dynamic glow popup toasts
        showToast(`🔔 ${data.title}: ${data.message}`, "info");
        // Play notification audio alert
        playNotificationSound();
        // Dynamic increments of bubble unread counts
        incrementUnreadBadge();
        // Refresh local cache and list if drawer is open
        const drawer = document.getElementById("header-notification-drawer");
        if (drawer && drawer.style.display === "flex") {
          fetchHeaderNotifications();
        }
      });
    }
  }, 1500);

  // Cross-tab synchronization via LocalStorage storage trigger
  window.addEventListener("storage", (e) => {
    if (e.key === "skillswap_notification_read_event") {
      fetchHeaderNotifications();
    }
  });
}

function playNotificationSound() {
  try {
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioContext.createOscillator();
    const gain = audioContext.createGain();
    osc.connect(gain);
    gain.connect(audioContext.destination);
    
    osc.type = "sine";
    osc.frequency.setValueAtTime(880, audioContext.currentTime); // High pitched clean bell note
    gain.gain.setValueAtTime(0.08, audioContext.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + 0.35);
    
    osc.start();
    osc.stop(audioContext.currentTime + 0.35);
  } catch (err) {
    // Audio context not allowed until interaction
  }
}

function incrementUnreadBadge() {
  const badge = document.getElementById("bell-unread-badge");
  if (!badge) return;
  let count = parseInt(badge.textContent || "0") + 1;
  badge.textContent = count;
  badge.style.display = "inline-flex";
}

function fetchHeaderNotifications() {
  if (typeof API === "undefined" || !localStorage.getItem("skillswap_access_token")) return;
  
  API.get("/notifications?unread=true").then((notes) => {
    const badge = document.getElementById("bell-unread-badge");
    const list = document.getElementById("drawer-notifications-list");
    if (!badge || !list) return;

    // Set badge count
    if (notes.length > 0) {
      badge.textContent = notes.length;
      badge.style.display = "inline-flex";
    } else {
      badge.style.display = "none";
    }

    if (notes.length === 0) {
      list.innerHTML = `<div style="padding:2rem;text-align:center;color:var(--text-secondary);font-size:0.85rem">No unread alerts found</div>`;
      return;
    }

    // Render unread notifications in drawer
    list.innerHTML = notes.slice(0, 8).map((n) => {
      // Color coded priority indicator
      let leftBorder = "2px solid var(--accent)";
      if (n.priority === "high") leftBorder = "3px solid var(--danger)";
      else if (n.priority === "normal" || n.priority === "medium") leftBorder = "2px solid var(--warning)";

      return `
        <div onclick="readAndNavigateNotification(event, ${n.id}, '${n.link || ""}')" style="padding:0.75rem 1rem;border-bottom:1px solid var(--border);border-left:${leftBorder};background:rgba(255,255,255,0.01);cursor:pointer;transition:background 0.2s" onmouseover="this.style.background='rgba(255,255,255,0.04)'" onmouseout="this.style.background='rgba(255,255,255,0.01)'">
          <div style="font-size:0.82rem;font-weight:700;color:var(--text-primary);margin-bottom:0.15rem">${escapeHtml(n.title)}</div>
          <div style="font-size:0.75rem;color:var(--text-secondary);line-height:1.3">${escapeHtml(n.message)}</div>
          <div style="font-size:0.62rem;color:var(--text-secondary);margin-top:0.25rem;text-align:right">${new Date(n.created_at).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}</div>
        </div>
      `;
    }).join("");
  }).catch(() => {});
}

function readAndNavigateNotification(event, nid, link) {
  if (event) event.stopPropagation();
  
  // Call API to mark read
  API.put(`/notifications/${nid}/read`, {}).then(() => {
    // Trigger Storage Event for cross-tab sync
    localStorage.setItem("skillswap_notification_read_event", Date.now().toString());
    
    // Refresh bell drawer
    fetchHeaderNotifications();
    
    // Navigate if link exists
    if (link) {
      window.location.href = link;
    }
  }).catch((err) => {
    showToast("Failed to clear notification: " + err.message, "error");
  });
}

function markAllNotificationsRead(event) {
  if (event) event.stopPropagation();
  if (typeof API === "undefined") return;

  API.put("/notifications/read-all", {}).then(() => {
    showToast("All notifications cleared!", "success");
    localStorage.setItem("skillswap_notification_read_event", Date.now().toString());
    fetchHeaderNotifications();
  }).catch((err) => {
    showToast("Failed to clear notifications: " + err.message, "error");
  });
}

function escapeHtml(str) {
  return String(str || "").replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}
