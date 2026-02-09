requireAuth();

async function loadMe(){
  const u = getUser();
  meBox.innerHTML = `<b>${u.full_name}</b><br/>${u.email}<br/>Role: ${u.role}`;
}

async function loadChart(){
  const u = getUser();
  if(u.role !== "ADMIN"){
    note.innerText = "Admin analytics chart is only available for ADMIN role.";
    return;
  }

  const res = await apiFetch("/internships/admin/analytics/", {method:"GET"});
  const data = await res.json().catch(()=>({}));
  if(!res.ok){ note.innerText = "Failed to load analytics"; return; }

  const c = data.counts;
  const ctx = document.getElementById("chart");
  new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Interns", "Supervisors", "Tasks", "Open Complaints"],
      datasets: [{
        label: "Counts",
        data: [c.interns, c.supervisors, c.tasks_total, c.complaints_open],
      }]
    }
  });
}

loadMe();
loadChart();
