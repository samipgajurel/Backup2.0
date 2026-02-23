// frontend/js/api.js

const API_BASE = (window.API_BASE || "http://127.0.0.1:8000/api").replace(/\/+$/,"");

function apiUrl(path){
  if(!path.startsWith("/")) path = "/" + path;
  return API_BASE + path;
}

function getAccess(){
  let t = localStorage.getItem("access") || "";
  t = t.replace(/^Bearer\s+/i, "").trim();
  // remove accidental quotes
  if ((t.startsWith('"') && t.endsWith('"')) || (t.startsWith("'") && t.endsWith("'"))) {
    t = t.slice(1, -1).trim();
  }
  return t;
}

function getRefresh(){
  let t = localStorage.getItem("refresh") || "";
  t = t.replace(/^Bearer\s+/i, "").trim();
  if ((t.startsWith('"') && t.endsWith('"')) || (t.startsWith("'") && t.endsWith("'"))) {
    t = t.slice(1, -1).trim();
  }
  return t;
}

async function refreshAccessToken(){
  const refresh = getRefresh();
  if(!refresh) return false;

  const res = await fetch(apiUrl("/token/refresh/"), {
    method: "POST",
    headers: { "Content-Type": "application/json", "Accept": "application/json" },
    body: JSON.stringify({ refresh })
  });

  if(!res.ok) return false;

  const data = await res.json().catch(()=>null);
  if(!data?.access) return false;

  localStorage.setItem("access", data.access);
  return true;
}

async function apiFetch(path, options = {}){
  let access = getAccess();

  const headers = new Headers(options.headers || {});
  headers.set("Accept", headers.get("Accept") || "application/json");

  // JSON body support
  if (options.body && typeof options.body === "string" && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  if (access && !headers.has("Authorization")) {
    headers.set("Authorization", "Bearer " + access);
  }

  let res = await fetch(apiUrl(path), { ...options, headers });

  // ✅ if access expired/invalid -> try refresh once
  if (res.status === 401) {
    const cloned = await res.clone().text().catch(()=> "");
    if (cloned.includes("token_not_valid") || cloned.includes("Given token not valid")) {
      const ok = await refreshAccessToken();
      if (ok) {
        access = getAccess();
        headers.set("Authorization", "Bearer " + access);
        res = await fetch(apiUrl(path), { ...options, headers });
      }
    }
  }

  return res;
}

// ✅ Download helper for CSV/PDF (works with JWT + refresh)
async function apiDownload(path, filename){
  // use apiFetch so refresh logic works
  const res = await apiFetch(path, { method: "GET", headers: { "Accept": "*/*" } });

  if(!res.ok){
    const text = await res.text().catch(()=> "");
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

window.apiFetch = apiFetch;
window.apiDownload = apiDownload;
window.API_BASE = API_BASE;