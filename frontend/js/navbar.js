// frontend/js/navbar.js
// Uses existing CSS classes: .navbar, .nav-inner, .nav-left, .nav-links, .nav-right, .logo, .badge
// Requires auth.js: getUser(), logout()

(function () {
  "use strict";

  function esc(s) {
    return String(s || "").replace(/[&<>"']/g, (m) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#039;",
    }[m]));
  }

  function activeFile() {
    return (location.pathname || "").split("/").pop() || "";
  }

  function linksFor(role) {
    const r = String(role || "").toUpperCase();

    if (r === "ADMIN") {
      return [
        ["admin_dashboard.html", "Dashboard"],
        ["admin_interns.html", "Interns"],
        ["admin_tasks.html", "Tasks"],
        ["admin_reports.html", "Reports"],
      ];
    }

    if (r === "SUPERVISOR") {
      return [
        ["dashboard.html", "Dashboard"],
        ["sup_tasks.html", "Tasks"],
        ["sup_rate.html", "Rate"],
        ["sup_reports.html", "Reports"],
      ];
    }

    // INTERN
    return [
      ["dashboard.html", "Dashboard"],
      ["intern_tasks.html", "My Tasks"],
      ["intern_reports.html", "Reports"],
      ["intern_complaints.html", "Complaints"],
    ];
  }

  function ensureMount() {
    let mount = document.getElementById("navbarMount");
    if (mount) return mount;

    mount = document.createElement("div");
    mount.id = "navbarMount";
    document.body.prepend(mount);
    return mount;
  }

  function renderNavbar() {
    const user = typeof window.getUser === "function" ? window.getUser() : null;
    if (!user) return;

    const mount = ensureMount();
    const active = activeFile();

    const role = esc(user.role || "");
    const name = esc(user.full_name || user.name || user.email || "User");
    const links = linksFor(user.role);

    const linksHtml = links.map(([href, label]) => {
      const isActive = href === active;
      return `
        <a href="${href}" style="${isActive ? 'border-color: rgba(79,140,255,.55); background: rgba(79,140,255,.10);' : ''}">
          ${esc(label)}
        </a>`;
    }).join("");

    mount.innerHTML = `
      <div class="navbar">
        <div class="nav-inner">
          <div class="nav-left">
            <a class="logo" href="dashboard.html">Codavatar InternTrack</a>
            <span class="badge">${role}</span>

            <div class="nav-links">
              ${linksHtml}
            </div>
          </div>

          <div class="nav-right">
            <span class="badge">${name}</span>
            <button class="btn-inline" type="button" id="logoutBtn">Logout</button>
          </div>
        </div>
      </div>
    `;

    const logoutBtn = document.getElementById("logoutBtn");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", () => {
        if (typeof window.logout === "function") window.logout();
        else {
          localStorage.clear();
          location.href = "login.html";
        }
      });
    }
  }

  window.renderNavbar = renderNavbar;
})();