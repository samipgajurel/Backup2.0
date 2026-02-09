const internsBox = document.getElementById("interns");
const supervisorsBox = document.getElementById("supervisors");
const msg = document.getElementById("msg");
const refreshBtn = document.getElementById("refreshBtn");

function showError(text) {
  msg.innerText = text;
  msg.className = "msg err";
  msg.style.display = "block";
}

function clearMsg() {
  msg.innerText = "";
  msg.style.display = "none";
}

function userCard(user) {
  const div = document.createElement("div");
  div.className = "user-card";

  div.innerHTML = `
    <div>
      <strong>${user.full_name || "-"}</strong><br/>
      <small>${user.email}</small>
    </div>
    <button class="btn-danger">Delete</button>
  `;

  div.querySelector("button").onclick = async () => {
    if (!confirm(`Delete ${user.email}?`)) return;

    const res = await apiFetch(`/accounts/admin/delete-user/${user.id}/`, {
      method: "DELETE",
    });

    if (!res.ok) {
      showError("Failed to delete user");
      return;
    }

    loadUsers();
  };

  return div;
}

async function loadUsers() {
  clearMsg();
  internsBox.innerHTML = "Loading…";
  supervisorsBox.innerHTML = "Loading…";

  try {
    const res = await apiFetch("/accounts/admin/users/", { method: "GET" });
    const data = await res.json();

    if (!res.ok) {
      showError(data.detail || "Failed to load users");
      internsBox.innerHTML = "Failed";
      supervisorsBox.innerHTML = "Failed";
      return;
    }

    internsBox.innerHTML = "";
    supervisorsBox.innerHTML = "";

    (data.interns || []).forEach(u =>
      internsBox.appendChild(userCard(u))
    );

    (data.supervisors || []).forEach(u =>
      supervisorsBox.appendChild(userCard(u))
    );

  } catch (err) {
    console.error(err);
    showError("Backend not reachable");
    internsBox.innerHTML = "Failed";
    supervisorsBox.innerHTML = "Failed";
  }
}

refreshBtn.onclick = loadUsers;
loadUsers();
