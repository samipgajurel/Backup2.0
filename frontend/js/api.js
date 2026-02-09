const API_BASE = "http://127.0.0.1:8000/api";

function clearSession() {
  localStorage.removeItem("access");
  localStorage.removeItem("refresh");
  localStorage.removeItem("user");
}

function logoutToLogin() {
  clearSession();
  window.location.href = "login.html";
}

async function refreshAccessToken() {
  const refresh = localStorage.getItem("refresh");
  if (!refresh) return false;

  const res = await fetch(`${API_BASE}/token/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });

  if (!res.ok) return false;

  const data = await res.json().catch(() => ({}));
  if (!data.access) return false;

  localStorage.setItem("access", data.access);
  return true;
}

async function apiFetch(path, options = {}) {
  const access = localStorage.getItem("access");

  const headers = {
    ...(options.headers || {}),
  };

  // ✅ Set JSON header only when body is plain object/string JSON, NOT FormData
  const isFormData = (typeof FormData !== "undefined") && (options.body instanceof FormData);
  if (options.body && !isFormData && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  if (access) headers["Authorization"] = `Bearer ${access}`;

  let res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  // ✅ If access token expired, try refresh once, then retry request
  if (res.status === 401) {
    const refreshed = await refreshAccessToken();
    if (!refreshed) {
      logoutToLogin();
      return res;
    }

    const newAccess = localStorage.getItem("access");
    const retryHeaders = {
      ...headers,
      Authorization: `Bearer ${newAccess}`,
    };

    res = await fetch(`${API_BASE}${path}`, { ...options, headers: retryHeaders });

    // If still 401 -> logout
    if (res.status === 401) {
      logoutToLogin();
      return res;
    }
  }

  return res;
}
