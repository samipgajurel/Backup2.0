// frontend/js/navbar.js

function renderNavbar() {
  const nav = document.getElementById("navbar");
  if (!nav) return;

  const user = (typeof getUser === "function") ? getUser() : null;
  const role = (user?.role || "GUEST").toUpperCase();

  const links = [];
  links.push({ label: "Dashboard", href: "dashboard.html" });

  if (role === "ADMIN") {
    links.push({ label: "Analytics", href: "admin_analytics.html" });
    links.push({ label: "Assign Interns", href: "admin_assign.html" });
    links.push({ label: "Attendance", href: "admin_attendance.html" });
    links.push({ label: "Complaints", href: "admin_complaints.html" });
    links.push({ label: "Monthly Reports", href: "admin_reports.html" });
    links.push({ label: "Activity Log", href: "admin_activity.html" });
    links.push({ label: "Users", href: "admin_users.html" });
  }

  if (role === "SUPERVISOR") {
    links.push({ label: "My Interns", href: "sup_interns.html" });

    // ✅ FIXED to match your folder screenshot:
    links.push({ label: "Create Task", href: "sup_create_tasks.html" });
    links.push({ label: "Tasks", href: "sup_task.html" });
    links.push({ label: "Rate/Feedback", href: "sup_rate.html" });

    links.push({ label: "Attendance", href: "sup_attendance.html" });
    links.push({ label: "Reports", href: "sup_reports.html" });
    links.push({ label: "Complaints", href: "sup_complaints.html" });
    links.push({ label: "Monthly Progress", href: "sup_monthly_progress.html" });
  }

  if (role === "INTERN") {
    links.push({ label: "My Tasks", href: "intern_tasks.html" });
    links.push({ label: "Task Status", href: "intern_status.html" });
    links.push({ label: "Submit Report", href: "intern_report.html" });
    links.push({ label: "Attendance", href: "intern_attendance.html" });
    links.push({ label: "Feedback", href: "intern_feedback.html" });
    links.push({ label: "My Supervisor", href: "intern_supervisor.html" });
    links.push({ label: "Complaints", href: "intern_complaints.html" });
  }

  nav.innerHTML = `
    <div class="navbar">
      <div class="nav-inner">
        <div class="nav-left">
          <a class="logo" href="dashboard.html">Codavatar InternTrack</a>
          <span class="badge">${role}${user?.full_name ? ` • ${user.full_name}` : ""}</span>
        </div>

        <div class="nav-links" id="navLinks"></div>

        <div class="nav-right">
          <button class="btn-inline" type="button" id="themeBtn">🌙/☀️ Theme</button>
          <button class="btn-inline" id="logoutBtn" type="button">Logout</button>
        </div>
      </div>
    </div>
  `;

  const navLinks = document.getElementById("navLinks");
  navLinks.innerHTML = links.map(l => `<a href="${l.href}">${l.label}</a>`).join("");

  // theme button
  const themeBtn = document.getElementById("themeBtn");
  themeBtn.addEventListener("click", () => {
    if (typeof toggleTheme === "function") toggleTheme();
  });

  // ✅ logout button always works
  const logoutBtn = document.getElementById("logoutBtn");
  logoutBtn.addEventListener("click", () => {
    if (typeof logout === "function") logout();
    else {
      localStorage.clear();
      window.location.replace("login.html");
    }
  });
}
