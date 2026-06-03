/** API and app configuration */
let origin = window.location.origin;
if (!origin || origin === 'null' || origin === 'file://' || origin.includes(':5500') || origin.includes(':3000')) {
  origin = 'http://localhost:5000';
}

const CONFIG = {
  API_BASE: origin + "/api",
  SOCKET_URL: origin,
  UPLOAD_BASE: origin + "/uploads/",
  TOKEN_KEY: "skillswap_access_token",
  USER_KEY: "skillswap_user",
};
