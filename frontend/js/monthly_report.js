// ===== CONFIG =====
const REPORT_ENDPOINT = "/reports/monthly/";
const CSV_ENDPOINT = "/reports/monthly/export/csv/";
const PDF_ENDPOINT = "/reports/monthly/export/pdf/";

// ===== DOM =====
const yearSel = document.getElementById("year");
const monthSel = document.getElementById("month");
const loadBtn = document.getElementById("loadBtn");
const exportCsvBtn = document.getElementById("exportCsvBtn");
const exportPdfBtn = document.getElementById("exportPdfBtn");
const resultDiv = document.getElementById("reportResult");
const msgDiv = document.getElementById("msg");

// ===== HELPERS =====
function showMsg(text, type = "ok") {
  msgDiv.textContent = text;
  msgDiv.className = type;
}

function qs() {
  const y = yearSel.value;
  const m = monthSel.value;
  return `?year=${encodeURIComponent(y)}&month=${encodeURIComponent(m)}`;
}

// ===== LOAD REPORT =====
async function loadReport() {
  showMsg("Loading report...", "ok");
  resultDiv.innerHTML = "";

  try {
    const res = await apiFetch(REPORT_ENDPOINT + qs(), {
      method: "GET"
    });

    if (!res.ok) {
      showMsg("Failed to load report (" + res.status + ")", "err");
      return;
    }

    const data = await res.json();

    resultDiv.innerHTML = `
      <h3>Monthly Report (${yearSel.value}-${monthSel.value})</h3>
      <p><strong>Total Interns:</strong> ${data.total_interns}</p>
      <p><strong>Total Tasks:</strong> ${data.total_tasks}</p>
      <p><strong>Completed Tasks:</strong> ${data.completed_tasks}</p>
      <p><strong>Pending Tasks:</strong> ${data.pending_tasks}</p>
    `;

    showMsg("Report loaded successfully.", "ok");

  } catch (err) {
    console.error(err);
    showMsg("Error loading report.", "err");
  }
}

// ===== EXPORT CSV =====
async function exportCSV() {
  showMsg("Downloading CSV...", "ok");

  try {
    const res = await apiFetch(CSV_ENDPOINT + qs(), {
      method: "GET"
    });

    if (!res.ok) {
      showMsg("Failed to download CSV (" + res.status + ")", "err");
      return;
    }

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = `monthly_report_${yearSel.value}_${monthSel.value}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();

    window.URL.revokeObjectURL(url);
    showMsg("CSV downloaded.", "ok");

  } catch (err) {
    console.error(err);
    showMsg("CSV download failed.", "err");
  }
}

// ===== EXPORT PDF =====
async function exportPDF() {
  showMsg("Downloading PDF...", "ok");

  try {
    const res = await apiFetch(PDF_ENDPOINT + qs(), {
      method: "GET"
    });

    if (!res.ok) {
      showMsg("Failed to download PDF (" + res.status + ")", "err");
      return;
    }

    const blob = await res.blob();
    const url = window.URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = `monthly_report_${yearSel.value}_${monthSel.value}.pdf`;
    document.body.appendChild(a);
    a.click();
    a.remove();

    window.URL.revokeObjectURL(url);
    showMsg("PDF downloaded.", "ok");

  } catch (err) {
    console.error(err);
    showMsg("PDF download failed.", "err");
  }
}

// ===== EVENTS =====
loadBtn.addEventListener("click", loadReport);
exportCsvBtn.addEventListener("click", exportCSV);
exportPdfBtn.addEventListener("click", exportPDF);