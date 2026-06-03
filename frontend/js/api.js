/**
 * Lightweight API client with:
 * - In-flight deduplication (GET only)
 * - 5-second response cache for GET requests (avoids redundant back-to-back calls)
 * - Automatic 401 → redirect to login
 */
const inflightRequests = {};
const _apiCache = {};     // endpoint -> { data, expires }
const _CACHE_TTL = 5000; // 5 seconds

function _apiCacheGet(key) {
  const entry = _apiCache[key];
  if (entry && Date.now() < entry.expires) return entry.data;
  delete _apiCache[key];
  return null;
}
function _apiCacheSet(key, data) {
  _apiCache[key] = { data, expires: Date.now() + _CACHE_TTL };
}
function _apiCacheInvalidate(prefix) {
  Object.keys(_apiCache).forEach(k => { if (k.startsWith(prefix)) delete _apiCache[k]; });
}

async function apiRequest(endpoint, options = {}) {
  const isGet = !options.method || options.method === "GET";

  // Serve cached GET response immediately
  if (isGet) {
    const cached = _apiCacheGet(endpoint);
    if (cached !== null) return cached;
    // Deduplicate concurrent identical requests
    if (inflightRequests[endpoint]) return inflightRequests[endpoint];
  }

  const promise = (async () => {
    try {
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

      // Store successful GET result in cache
      if (isGet) _apiCacheSet(endpoint, data);

      return data;
    } finally {
      if (isGet) delete inflightRequests[endpoint];
    }
  })();

  if (isGet) inflightRequests[endpoint] = promise;

  return promise;
}

const API = {
  get: (url) => apiRequest(url),
  post: (url, body) => { _apiCacheInvalidate(url.split('?')[0]); return apiRequest(url, { method: "POST", body: JSON.stringify(body) }); },
  put: (url, body) => { _apiCacheInvalidate(url.split('?')[0]); return apiRequest(url, { method: "PUT", body: JSON.stringify(body) }); },
  delete: (url) => { _apiCacheInvalidate(url.split('?')[0]); return apiRequest(url, { method: "DELETE" }); },
  upload: (url, formData) => apiRequest(url, { method: "POST", body: formData, headers: {} }),
  invalidateCache: (prefix) => _apiCacheInvalidate(prefix || ""),
};
