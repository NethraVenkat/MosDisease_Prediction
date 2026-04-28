const totalCount = document.getElementById("totalCount");
const lowCount = document.getElementById("lowCount");
const mediumCount = document.getElementById("mediumCount");
const highCount = document.getElementById("highCount");
const recentGrid = document.getElementById("recentGrid");

let pieChart = null;
let barChart = null;

function normalizeRisk(risk) {
  const v = String(risk || "").toLowerCase();
  if (v === "low" || v === "medium" || v === "high") return v;
  return null;
}

function resolveRisk(record) {
  return normalizeRisk(record.simulated_risk || record.predicted_risk || record.real_risk);
}

function toTitle(v) {
  return v ? v[0].toUpperCase() + v.slice(1) : "Unknown";
}

function formatTs(ts) {
  if (!ts) return "Unknown time";
  const d = new Date(ts);
  if (Number.isNaN(d.valueOf())) return String(ts);
  return d.toLocaleString();
}

function renderRecent(records) {
  if (!records.length) {
    recentGrid.innerHTML = '<p class="empty-note">No prediction records found yet.</p>';
    return;
  }

  recentGrid.innerHTML = records.slice(0, 8).map((record) => {
    const risk = resolveRisk(record) || "unknown";
    const label = toTitle(risk);
    return `
      <article class="prediction-card">
        <span class="risk-pill ${risk}">${label}</span>
        <div class="prediction-meta">
          <div><strong>Type:</strong> ${record.type || "prediction"}</div>
          <div><strong>Time:</strong> ${formatTs(record.timestamp)}</div>
        </div>
      </article>
    `;
  }).join("");
}

function renderCharts(counts) {
  const labels = ["Low", "Medium", "High"];
  const values = [counts.low, counts.medium, counts.high];
  const colors = ["rgba(67, 197, 158, 0.75)", "rgba(240, 177, 78, 0.75)", "rgba(239, 93, 121, 0.75)"];

  if (pieChart) pieChart.destroy();
  pieChart = new Chart(document.getElementById("riskPieChart"), {
    type: "pie",
    data: {
      labels,
      datasets: [{ data: values, backgroundColor: colors, borderColor: "rgba(7, 13, 24, 0.85)", borderWidth: 2 }],
    },
    options: {
      plugins: { legend: { labels: { color: "#d8e6ff" } } },
      maintainAspectRatio: false,
    },
  });

  if (barChart) barChart.destroy();
  barChart = new Chart(document.getElementById("riskBarChart"), {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "Risk count",
        data: values,
        backgroundColor: colors,
        borderRadius: 8,
      }],
    },
    options: {
      plugins: { legend: { labels: { color: "#d8e6ff" } } },
      scales: {
        x: { ticks: { color: "#c5d8f8" }, grid: { color: "rgba(255,255,255,0.05)" } },
        y: { ticks: { color: "#c5d8f8", precision: 0 }, grid: { color: "rgba(255,255,255,0.07)" } },
      },
      maintainAspectRatio: false,
    },
  });
}

async function loadDashboard() {
  const response = await fetch("/history");
  const payload = await response.json();

  if (!response.ok) {
    throw new Error(payload?.detail || "Failed to load history data");
  }

  const records = Array.isArray(payload.records) ? payload.records : [];
  const counts = { low: 0, medium: 0, high: 0 };

  for (const record of records) {
    const risk = resolveRisk(record);
    if (risk) counts[risk] += 1;
  }

  totalCount.textContent = String(records.length);
  lowCount.textContent = String(counts.low);
  mediumCount.textContent = String(counts.medium);
  highCount.textContent = String(counts.high);

  renderCharts(counts);
  renderRecent(records);
}

loadDashboard().catch((error) => {
  recentGrid.innerHTML = `<p class="empty-note">${error.message}</p>`;
});
