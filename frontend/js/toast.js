/** Toast notification system */
function showToast(message, type = "info") {
  let container = document.getElementById("toast-container");
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    // Sleek container styling
    container.style.position = "fixed";
    container.style.top = "20px";
    container.style.right = "20px";
    container.style.zIndex = "99999";
    container.style.display = "flex";
    container.style.flexDirection = "column";
    container.style.gap = "10px";
    document.body.appendChild(container);
  }
  const el = document.createElement("div");
  el.className = `toast ${type}`;
  
  // Sleek toast styling
  const colors = {
    info: "var(--accent, #00f2fe)",
    success: "var(--success, #10b981)",
    error: "var(--danger, #ef4444)",
    warning: "var(--warning, #f59e0b)"
  };
  const color = colors[type] || colors.info;
  
  el.style.background = "rgba(10, 10, 15, 0.95)";
  el.style.backdropFilter = "blur(10px)";
  el.style.border = `1px solid ${color}`;
  el.style.borderLeft = `4px solid ${color}`;
  el.style.color = "#fff";
  el.style.padding = "12px 20px";
  el.style.borderRadius = "8px";
  el.style.boxShadow = `0 8px 32px rgba(0, 0, 0, 0.3), 0 0 10px ${color}33`;
  el.style.fontFamily = "var(--font-main, sans-serif)";
  el.style.fontSize = "0.9rem";
  el.style.fontWeight = "500";
  el.style.opacity = "0";
  el.style.transform = "translateX(50px) scale(0.9)";
  el.style.transition = "all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)";
  
  // Icon based on type
  const icons = { info: "ℹ️", success: "✅", error: "❌", warning: "⚠️" };
  el.innerHTML = `<div style="display: flex; align-items: center; gap: 10px;">
    <span>${icons[type] || icons.info}</span>
    <span>${message}</span>
  </div>`;
  
  container.appendChild(el);
  
  // Trigger animation
  requestAnimationFrame(() => {
    el.style.opacity = "1";
    el.style.transform = "translateX(0) scale(1)";
  });
  
  setTimeout(() => {
    el.style.opacity = "0";
    el.style.transform = "translateX(50px) scale(0.9)";
    setTimeout(() => el.remove(), 400);
  }, 4000);
}
