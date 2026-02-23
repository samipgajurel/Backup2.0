// frontend/js/api.js

// Base API URL (strip trailing slashes)
const API_BASE = (window.API_BASE || "http://127.0.0.1:8000/api").replace(/\/+$/, "");

function apiUrl(path) {
  if (!path) path = "/";
  if (!path.startsWith("/")) path = "/" + path;
  return API_BASE + path;
}

async function apiFetch(path, options = {}) {
  const access = localStorage.getItem("access");

  const headers = new Headers(options.headers || {});
  headers.set("Accept", headers.get("Accept") || "application/json");

  // If body is a plain object, convert to JSON automatically
  if (options.body && typeof options.body === "object" && !(options.body instanceof FormData)) {
    if (!headers.has("Content-Type")) headers.set("Content-Type", "application/json");
    options = { ...options, body: JSON.stringify(options.body) };
  }

  // If body is already a JSON string and no content-type set, set it
  if (options.body && typeof options.body === "string" && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  // Add JWT
  if (access && !headers.has("Authorization")) {
    headers.set("Authorization", "Bearer " + access);
  }

  return fetch(apiUrl(path), { ...options, headers });
}

/**
 * Download helper for CSV/PDF/etc WITH JWT
 * Example:
 *   await apiDownload("/internships/admin/reports/monthly/csv/?year=2026&month=2", "report.csv")
 */
async function apiDownload(path, filename) {
  const access = localStorage.getItem("access");

  const res = await fetch(apiUrl(path), {
    method: "GET",
    headers: {
      "Authorization": access ? ("Bearer " + access) : "",
      "Accept": "*/*"
    }
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`Download failed ${res.status}: ${text || "No response body"}`);
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

window.apiFetch = apiFetch;
window.apiDownload = apiDownload;
window.API_BASE = API_BASE;