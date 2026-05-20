/** HTTP API client with JWT */
async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem(CONFIG.TOKEN_KEY);
  const headers = { ...(options.headers || {}) };

  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = headers["Content-Type"] || "application/json";
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${CONFIG.API_BASE}${endpoint}`, {
    ...options,
    headers,
    credentials: "include",
  });

  let data = {};
  try {
    data = await res.json();
  } catch (_) {}

  if (res.status === 401) {
    localStorage.removeItem(CONFIG.TOKEN_KEY);
    localStorage.removeItem(CONFIG.USER_KEY);
    if (!window.location.pathname.includes("login")) {
      window.location.href = "/frontend/pages/public/login.html";
    }
  }

  if (!res.ok) {
    throw new Error(data.error || data.message || "Request failed");
  }

  return data;
}

const API = {
  get: (url) => apiRequest(url),
  post: (url, body) => apiRequest(url, { method: "POST", body: JSON.stringify(body) }),
  put: (url, body) => apiRequest(url, { method: "PUT", body: JSON.stringify(body) }),
  delete: (url) => apiRequest(url, { method: "DELETE" }),
  upload: (url, formData) => apiRequest(url, { method: "POST", body: formData, headers: {} }),
};
