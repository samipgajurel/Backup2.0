// frontend/js/api.js

const API_BASE = (window.API_BASE || "http://127.0.0.1:8000/api").replace(/\/+$/,"");

function apiUrl(path){
  if(!path.startsWith("/")) path = "/" + path;
  return API_BASE + path;
}

async function apiFetch(path, options = {}){
  const access = localStorage.getItem("access");

  const headers = new Headers(options.headers || {});
  headers.set("Accept", "application/json");

  // JSON body support
  if (options.body && typeof options.body === "string" && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  // ✅ add JWT
  if (access && !headers.has("Authorization")) {
    headers.set("Authorization", "Bearer " + access);
  }

  return fetch(apiUrl(path), { ...options, headers });
}

// ✅ Download helper for CSV/PDF
async function apiDownload(path, filename){
  const access = localStorage.getItem("access");

  const res = await fetch(apiUrl(path), {
    method: "GET",
    headers: {
      "Authorization": access ? ("Bearer " + access) : "",
      "Accept": "*/*"
    }
  });

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


async function apiDownload(path, filename){
  const access = localStorage.getItem("access");
  const res = await fetch(API_BASE + path, {
    method: "GET",
    headers: { "Authorization": "Bearer " + access }
  });

  if(!res.ok){
    const t = await res.text().catch(()=> "");
    throw new Error(t || ("Failed: " + res.status));
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
}