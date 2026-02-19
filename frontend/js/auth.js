// frontend/js/auth.js
// Session + auth helpers + password helpers (FULL FIXED FILE)

(function () {
  "use strict";

  // -------------------- Session helpers --------------------

  function getUser() {
    const u = localStorage.getItem("user");
    try {
      return u ? JSON.parse(u) : null;
    } catch {
      return null;
    }
  }

  /**
   * Save session pieces:
   * setSession({ access, refresh, user })
   * Any field can be omitted.
   */
  function setSession({ access, refresh, user } = {}) {
    if (access) localStorage.setItem("access", access);
    if (refresh) localStorage.setItem("refresh", refresh);
    if (user) localStorage.setItem("user", JSON.stringify(user));
  }

  /**
   * Require logged-in session (access token + user object).
   * Redirects to login.html if missing.
   */
  function requireAuthOrRedirect() {
    const access = localStorage.getItem("access");
    const user = getUser();

    if (!access || !user) {
      window.location.href = "login.html";
      return null;
    }
    return user;
  }

  /**
   * Require a specific role ("ADMIN" | "SUPERVISOR" | "INTERN").
   * Redirects to dashboard.html if role mismatch.
   */
  function requireRole(role) {
    const user = requireAuthOrRedirect();
    if (!user) return null;

    if ((user.role || "").toUpperCase() !== String(role).toUpperCase()) {
      alert("Access denied: insufficient permissions.");
      window.location.href = "dashboard.html";
      return null;
    }
    return user;
  }

  function logout() {
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
    localStorage.removeItem("user");
    window.location.href = "login.html";
  }

  // -------------------- UI message helpers --------------------

  function showMsg(el, text, type = "") {
    if (!el) return;
    el.className = "msg show" + (type ? " " + type : "");
    el.textContent = text;
  }

  function hideMsg(el) {
    if (!el) return;
    el.className = "msg";
    el.textContent = "";
  }

  // -------------------- Password helpers (FIX for Show button + meter) --------------------

  function togglePassword(inputId, buttonId) {
    const input = document.getElementById(inputId);
    const btn = document.getElementById(buttonId);

    if (!input || !btn) {
      console.warn("togglePassword(): missing element", { inputId, buttonId });
      return;
    }

    btn.addEventListener("click", () => {
      const isHidden = input.type === "password";
      input.type = isHidden ? "text" : "password";
      btn.textContent = isHidden ? "Hide" : "Show";
    });
  }

  function passwordChecks(pw) {
    const s = String(pw || "");
    return {
      len: s.length >= 8,
      upper: /[A-Z]/.test(s),
      num: /[0-9]/.test(s),
      special: /[^A-Za-z0-9]/.test(s),
    };
  }

  function passwordStrong(pw) {
    const c = passwordChecks(pw);
    return c.len && c.upper && c.num && c.special;
  }

  // -------------------- Export globals (so inline scripts can call them) --------------------

  window.getUser = getUser;
  window.setSession = setSession;
  window.requireAuthOrRedirect = requireAuthOrRedirect;
  window.requireRole = requireRole;
  window.logout = logout;

  window.showMsg = showMsg;
  window.hideMsg = hideMsg;

  window.togglePassword = togglePassword;
  window.passwordChecks = passwordChecks;
  window.passwordStrong = passwordStrong;
})();
