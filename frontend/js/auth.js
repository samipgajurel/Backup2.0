// frontend/js/auth.js

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

/* Optional tiny helpers used in some pages */
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
// frontend/js/auth.js

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

/* Optional tiny helpers used in some pages */
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
window.getUser = getUser;
window.setSession = setSession;
window.requireAuthOrRedirect = requireAuthOrRedirect;
window.requireRole = requireRole;
window.logout = logout;
window.showMsg = showMsg;
window.hideMsg = hideMsg;