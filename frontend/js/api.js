// frontend/js/api.js

/**
 * Dokploy "single-domain" setup:
 * - Frontend served by Nginx at:  https://yourdomain.com/
 * - Backend proxied by Nginx at:   https://yourdomain.com/api/  -> http://backend:8000/
 *
 * So API_BASE should be "/api" in production.
 * If you ever want to use a separate API domain, you can set:
 *   window.API_BASE = "https://api.yourdomain.com/api"
 * before this script loads.
 */

// Prefer runtime override if provided, otherwise default to "/api"
const DEFAULT_API_BASE = "/api";
const API_BASE = (window.API_BASE || DEFAULT_API_BASE).replace(/\/+$/, "");

// Build final URL safely
function apiUrl(path) {
  if (!path) path = "/";
  if (!path.startsWith("/")) path = "/" + path;

  // If API_BASE is absolute (https://...), join normally
  // If API_BASE is relative (/api), still works
  return API_BASE + path;
}

function normalizeToken(raw) {
  let t = raw || "";
  t = String(t).replace(/^Bearer\s+/i, "").trim();

  // remove accidental quotes
  if (
    (t.startsWith('"') && t.endsWith('"')) ||
    (t.startsWith("'") && t.endsWith("'"))
  ) {
    t = t.slice(1, -1).trim();
  }
  return t;
}

function getAccess() {
  return normalizeToken(localStorage.getItem("access") || "");
}

function getRefresh() {
  return normalizeToken(localStorage.getItem("refresh") || "");
}

async function refreshAccessToken() {
  const refresh = getRefresh();
  if (!refresh) return false;

  const res = await fetch(apiUrl("/token/refresh/"), {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "Accept": "application/json",
    },
    body: JSON.stringify({ refresh }),
  });

  if (!res.ok) return false;

  const data = await res.json().catch(() => null);
  if (!data || !data.access) return false;

  localStorage.setItem("access", data.access);
  return true;
}

async function apiFetch(path, options = {}) {
  let access = getAccess();

  // Use Headers object so we can mutate safely
  const headers = new Headers(options.headers || {});
  headers.set("Accept", headers.get("Accept") || "application/json");

  // Auto-set JSON if string body is provided
  if (options.body && typeof options.body === "string" && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  // Attach token if available and not already set
  if (access && !headers.has("Authorization")) {
    headers.set("Authorization", "Bearer " + access);
  }

  let res = await fetch(apiUrl(path), { ...options, headers });

  // If access expired/invalid -> try refresh once, then retry
  if (res.status === 401) {
    const clonedText = await res.clone().text().catch(() => "");
    const tokenInvalid =
      clonedText.includes("token_not_valid") ||
      clonedText.includes("Given token not valid") ||
      clonedText.includes("token is invalid") ||
      clonedText.includes("Token is invalid");

    if (tokenInvalid) {
      const ok = await refreshAccessToken();
      if (ok) {
        access = getAccess();
        if (access) headers.set("Authorization", "Bearer " + access);
        res = await fetch(apiUrl(path), { ...options, headers });
      }
    }
  }

  return res;
}

// Download helper for CSV/PDF (works with JWT + refresh)
async function apiDownload(path, filename) {
  const res = await apiFetch(path, {
    method: "GET",
    headers: { "Accept": "*/*" },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Download failed ${res.status}: ${text}`);
  }

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = url;
  a.download = filename || "download";
  document.body.appendChild(a);
  a.click();
  a.remove();

  URL.revokeObjectURL(url);
  return true;
}

// expose globally (your HTML uses apiFetch directly)
window.apiFetch = apiFetch;
window.apiDownload = apiDownload;
window.API_BASE = API_BASE;