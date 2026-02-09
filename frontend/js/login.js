// frontend/js/login.js
// Requires: js/api.js, js/auth.js, js/theme.js (optional)
// Works with your login.html that has:
//   email input id="name"
//   password input id="password"
//   toggle button id="pwToggleBtn"
//   login button id="loginBtn"
//   message box id="msg"

(function () {
  // --- Grab elements (match your HTML) ---
  const msg = document.getElementById("msg");
  const form = document.getElementById("form");
  const emailInput = document.getElementById("name");      // <-- your login.html uses id="name"
  const passwordInput = document.getElementById("password");
  const toggleBtn = document.getElementById("pwToggleBtn");
  const loginBtn = document.getElementById("loginBtn");

  // Safety checks (avoid null errors)
  if (!emailInput || !passwordInput || !loginBtn) {
    console.error("login.js: Missing required HTML ids (name/password/loginBtn).");
    return;
  }

  // --- Helpers (compatible with your style.css msg classes) ---
  function showMsg(text, type = "") {
    if (!msg) return;
    msg.className = "msg show" + (type ? " " + type : "");
    msg.textContent = text;
  }

  function hideMsg() {
    if (!msg) return;
    msg.className = "msg";
    msg.textContent = "";
  }

  function setLoading(isLoading) {
    loginBtn.disabled = isLoading;
    loginBtn.textContent = isLoading ? "Logging in..." : "Login";
  }

  // --- Show/Hide password ---
  function togglePassword() {
    const hidden = passwordInput.type === "password";
    passwordInput.type = hidden ? "text" : "password";
    if (toggleBtn) toggleBtn.textContent = hidden ? "Hide" : "Show";
  }

  // Make sure inline onclick won't break (if you still have it somewhere)
  window.togglePassword = togglePassword;

  if (toggleBtn) {
    toggleBtn.addEventListener("click", togglePassword);
  }

  // --- Login logic ---
  async function doLogin() {
    hideMsg();

    const email = (emailInput.value || "").trim().toLowerCase();
    const password = passwordInput.value || "";

    if (!email || !password) {
      showMsg("Email and password are required.", "err");
      return;
    }

    setLoading(true);

    try {
      // IMPORTANT: Your backend is mounted at /api/token/
      // Your apiFetch already prepends API_BASE ("http://127.0.0.1:8000/api")
      const tokenRes = await apiFetch("/token/", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      const tokenData = await tokenRes.json().catch(() => ({}));

      if (!tokenRes.ok) {
        showMsg(tokenData.detail || "Invalid credentials.", "err");
        return;
      }

      // Store tokens using your auth.js helper if available; fallback if not
      if (typeof setSession === "function") {
        setSession({ access: tokenData.access, refresh: tokenData.refresh });
      } else {
        localStorage.setItem("access", tokenData.access);
        localStorage.setItem("refresh", tokenData.refresh);
      }

      // Fetch user profile
      const meRes = await apiFetch("/accounts/me/", { method: "GET" });
      const me = await meRes.json().catch(() => ({}));

      if (!meRes.ok) {
        showMsg(me.detail || "Login ok, but profile fetch failed.", "err");
        return;
      }

      if (typeof setSession === "function") {
        setSession({ user: me });
      } else {
        localStorage.setItem("user", JSON.stringify(me));
      }

      // Go dashboard
      window.location.href = "dashboard.html";
    } catch (err) {
      console.error(err);
      showMsg("Backend not reachable. Is Django running?", "err");
    } finally {
      setLoading(false);
    }
  }

  // Click login
  loginBtn.addEventListener("click", doLogin);

  // Enter key inside form submits once
  if (form) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      doLogin();
    });

    // If your button is type="button" (it is), Enter won’t submit by default.
    // So we listen for Enter on inputs:
    form.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        doLogin();
      }
    });
  } else {
    // fallback: Enter anywhere
    document.addEventListener("keydown", (e) => {
      if (e.key === "Enter") doLogin();
    });
  }
})();
