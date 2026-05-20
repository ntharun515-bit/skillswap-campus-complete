/** Dark/light theme toggle */
function initTheme() {
  const saved = localStorage.getItem("skillswap_theme") || "light";
  document.documentElement.setAttribute("data-theme", saved);
  updateThemeIcon(saved);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") || "light";
  const next = current === "light" ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("skillswap_theme", next);
  updateThemeIcon(next);
}

function updateThemeIcon(theme) {
  document.querySelectorAll(".theme-toggle").forEach((btn) => {
    btn.textContent = theme === "light" ? "🌙" : "☀️";
  });
}

document.addEventListener("DOMContentLoaded", initTheme);
