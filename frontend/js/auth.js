/** Authentication helpers */
function saveSession(data) {
  if (data.access_token) {
    localStorage.setItem(CONFIG.TOKEN_KEY, data.access_token);
  }
  if (data.user) {
    localStorage.setItem(CONFIG.USER_KEY, JSON.stringify(data.user));
  }
}

function getUser() {
  try {
    return JSON.parse(localStorage.getItem(CONFIG.USER_KEY) || "null");
  } catch {
    return null;
  }
}

function isLoggedIn() {
  return !!localStorage.getItem(CONFIG.TOKEN_KEY);
}

function requireAuth(roles = []) {
  if (!isLoggedIn()) {
    window.location.href = "/frontend/pages/public/login.html";
    return false;
  }
  const user = getUser();
  if (roles.length && user && !roles.includes(user.role)) {
    redirectByRole(user.role);
    return false;
  }
  return true;
}

function redirectByRole(role) {
  const map = {
    student: "/frontend/pages/student/dashboard.html",
    client: "/frontend/pages/client/dashboard.html",
    admin: "/frontend/pages/admin/dashboard.html",
  };
  window.location.href = map[role] || "/";
}

async function logout() {
  try {
    await API.post("/auth/logout", {});
  } catch (_) {}
  localStorage.removeItem(CONFIG.TOKEN_KEY);
  localStorage.removeItem(CONFIG.USER_KEY);
  window.location.href = "/frontend/pages/public/index.html";
}
