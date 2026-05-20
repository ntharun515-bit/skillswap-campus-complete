/** Shared dashboard page bootstrap */
function initDashboard(role, active, title, onReady) {
  if (!requireAuth([role])) return;
  const app = document.getElementById("app");
  app.innerHTML =
    renderSidebar(role, active) +
    '<main class="dashboard-main">' +
    renderDashboardHeader(title) +
    '<div class="dashboard-content" id="page-content"></div></main>';
  app.className = "dashboard-layout";
  if (typeof initSocket === "function") initSocket();
  if (typeof onReady === "function") onReady(document.getElementById("page-content"));
}

function initPublicPage(navActive, bodyHtml, onReady) {
  document.getElementById("nav").innerHTML = renderNavbar(navActive);
  document.getElementById("footer").innerHTML = renderFooter();
  const main = document.getElementById("main");
  if (main) main.innerHTML = bodyHtml;
  if (typeof onReady === "function") onReady();
}
