const apiStatus = document.getElementById("apiStatus");
const schemaStatus = document.getElementById("schemaStatus");
const latestRecord = document.getElementById("latestRecord");
const schemaNotice = document.getElementById("schemaNotice");
const featureForm = document.getElementById("featureForm");
const resultEmpty = document.getElementById("resultEmpty");
const resultCard = document.getElementById("resultCard");
const historyList = document.getElementById("historyList");
const riskAlert = document.getElementById("riskAlert");
const solutionsNavLink = document.getElementById("solutionsNavLink");
const chartNotice = document.getElementById("chartNotice");
const riskDistributionCanvas = document.getElementById("riskDistributionChart");
const riskTrendCanvas = document.getElementById("riskTrendChart");

let featureCols = [];
let riskDistributionChart = null;
let riskTrendChart = null;

function guessValue(name) {
  const lower = name.toLowerCase();
  if (lower.includes("temp")) return 30;
  if (lower.includes("humid")) return 80;
  if (lower.includes("rain") || lower.includes("precip")) return 120;
  if (lower.includes("wind")) return 5;
  if (lower.includes("case") || lower.includes("count")) return 10;
  return 0;
}

function labelFromName(name) {
  return name.replace(/_/g, " ");
}

function formatValue(value) {
  if (value === null || value === undefined) return "-";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function normalizeRisk(value) {
  const risk = String(value || "").toLowerCase();
  if (risk === "high") return "High";
  if (risk === "medium") return "Medium";
  if (risk === "low") return "Low";
  return null;
}

function updateSolutionsLink(risk) {
  const level = normalizeRisk(risk);
  if (!level) return;

  window.localStorage.setItem("predictedRisk", level);

  if (solutionsNavLink) {
    solutionsNavLink.href = `/solutions?risk=${encodeURIComponent(level)}`;
  }
}

function extractRisk(record) {
  return (
    record.simulated_risk ||
    record.predicted_risk ||
    record.real_risk ||
    null
  );
}

function normalizeRiskKey(value) {
  const normalized = normalizeRisk(value);
  return normalized ? normalized.toLowerCase() : null;
}

function updateChartNotice(show) {
  if (!chartNotice) return;
  if (show) {
    chartNotice.classList.remove("hidden");
    chartNotice.textContent = "No chart data available yet.";
  } else {
    chartNotice.classList.add("hidden");
    chartNotice.textContent = "";
  }
}

function destroyCharts() {
  if (riskDistributionChart) {
    riskDistributionChart.destroy();
    riskDistributionChart = null;
  }
  if (riskTrendChart) {
    riskTrendChart.destroy();
    riskTrendChart = null;
  }
}

function renderCharts(records) {
  if (typeof Chart === "undefined" || !riskDistributionCanvas || !riskTrendCanvas) {
    updateChartNotice(true);
    return;
  }

  const riskValues = records
    .map((record) => normalizeRiskKey(extractRisk(record)))
    .filter(Boolean);

  if (!riskValues.length) {
    destroyCharts();
    updateChartNotice(true);
    return;
  }

  updateChartNotice(false);

  const distribution = { low: 0, medium: 0, high: 0 };
  for (const risk of riskValues) distribution[risk] += 1;

  const labels = ["Low", "Medium", "High"];
  const data = [distribution.low, distribution.medium, distribution.high];
  const colorMap = {
    Low: "rgba(86, 214, 197, 0.75)",
    Medium: "rgba(255, 184, 107, 0.75)",
    High: "rgba(255, 107, 136, 0.75)",
  };

  if (riskDistributionChart) riskDistributionChart.destroy();
  riskDistributionChart = new Chart(riskDistributionCanvas, {
    type: "doughnut",
    data: {
      labels,
      datasets: [{
        data,
        backgroundColor: labels.map((label) => colorMap[label]),
        borderColor: "rgba(8, 17, 31, 0.85)",
        borderWidth: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: "#d3e3ff" } },
      },
    },
  });

  const recent = records.slice(0, 12).reverse();
  const trendLabels = recent.map((record, index) => {
    if (record.timestamp) {
      const dt = new Date(record.timestamp);
      if (!Number.isNaN(dt.valueOf())) {
        return dt.toLocaleDateString(undefined, { month: "short", day: "numeric" });
      }
    }
    return `R${index + 1}`;
  });

  const trendData = recent.map((record) => {
    const risk = normalizeRiskKey(extractRisk(record));
    if (risk === "high") return 3;
    if (risk === "medium") return 2;
    return 1;
  });

  if (riskTrendChart) riskTrendChart.destroy();
  riskTrendChart = new Chart(riskTrendCanvas, {
    type: "line",
    data: {
      labels: trendLabels,
      datasets: [{
        label: "Risk level",
        data: trendData,
        borderColor: "rgba(120, 166, 255, 0.95)",
        backgroundColor: "rgba(120, 166, 255, 0.2)",
        pointBackgroundColor: "rgba(86, 214, 197, 0.95)",
        pointRadius: 4,
        borderWidth: 2,
        fill: true,
        tension: 0.28,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          min: 1,
          max: 3,
          ticks: {
            color: "#d3e3ff",
            stepSize: 1,
            callback: (value) => {
              if (value === 1) return "Low";
              if (value === 2) return "Medium";
              if (value === 3) return "High";
              return "";
            },
          },
          grid: { color: "rgba(255,255,255,0.08)" },
        },
        x: {
          ticks: { color: "#b8c9e8" },
          grid: { color: "rgba(255,255,255,0.04)" },
        },
      },
      plugins: {
        legend: { labels: { color: "#d3e3ff" } },
      },
    },
  });
}

function updateRiskAlert(level, source) {
  if (!riskAlert) return;

  riskAlert.classList.remove("low", "medium");

  if (!level) {
    riskAlert.classList.add("hidden");
    riskAlert.textContent = "";
    return;
  }

  const normalized = String(level).toLowerCase();
  riskAlert.classList.remove("hidden");

  if (normalized === "high") {
    riskAlert.textContent = `High Risk Alert: ${source} indicates HIGH outbreak risk. Act immediately.`;
    return;
  }

  if (normalized === "medium") {
    riskAlert.classList.add("medium");
    riskAlert.textContent = `Moderate Risk: ${source} indicates MEDIUM outbreak risk.`;
    return;
  }

  riskAlert.classList.add("low");
  riskAlert.textContent = `Low Risk: ${source} indicates LOW outbreak risk.`;
}

async function api(path, method = "GET", body) {
  const options = { method, headers: { "Content-Type": "application/json" } };
  if (body) options.body = JSON.stringify(body);
  const response = await fetch(path, options);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload?.detail || payload?.message || "Request failed");
  }
  return payload;
}

function setStatus(element, text, tone = "") {
  element.textContent = text;
  element.className = tone ? tone : "";
}

function renderForm(columns) {
  featureForm.innerHTML = columns.map((column) => `
    <label class="field">
      <span>${labelFromName(column)}</span>
      <input
        name="${column}"
        type="number"
        step="0.01"
        value="${guessValue(column)}"
        placeholder="0"
      />
    </label>
  `).join("");
}

function readFeatures() {
  const data = {};
  for (const column of featureCols) {
    const input = featureForm.elements.namedItem(column);
    data[column] = Number(input.value || 0);
  }
  return data;
}

function renderResult(title, data) {
  resultEmpty.classList.add("hidden");
  resultCard.classList.remove("hidden");

  const tone = data?.simulated_risk || data?.predicted_risk || data?.real_risk || "neutral";
  updateRiskAlert(tone, title);
  const solutionRisk = normalizeRisk(tone);
  updateSolutionsLink(solutionRisk);

  const solutionsHref = solutionRisk
    ? `/solutions?risk=${encodeURIComponent(solutionRisk)}`
    : "/solutions";

  resultCard.innerHTML = `
    <div class="result-header ${String(tone).toLowerCase()}">
      <span>${title}</span>
      <strong>${formatValue(data?.simulated_risk || data?.predicted_risk)}</strong>
    </div>
    <div class="result-grid">
      ${Object.entries(data).map(([key, value]) => `
        <div class="result-item">
          <span>${labelFromName(key)}</span>
          <strong>${formatValue(value)}</strong>
        </div>
      `).join("")}
    </div>
    <a class="solution-link" href="${solutionsHref}">View Recommended Solutions</a>
  `;
}

async function loadSchema() {
  const data = await api("/schema");
  featureCols = data.feature_cols || [];

  if (!featureCols.length) {
    schemaNotice.textContent = "No feature columns were returned by the API.";
    setStatus(schemaStatus, "Unavailable");
    return;
  }

  renderForm(featureCols);
  schemaNotice.textContent = `${featureCols.length} feature columns loaded from the model.`;
  setStatus(schemaStatus, `${featureCols.length} fields ready`, "good");
}

async function loadHealth() {
  try {
    const data = await api("/health");
    setStatus(apiStatus, data.message || "API running", "good");
  } catch (error) {
    setStatus(apiStatus, "Offline", "bad");
  }
}

async function runPrediction() {
  const features = readFeatures();
  const data = await api("/predict", "POST", { features });
  renderResult("Prediction", data);
  latestRecord.textContent = data.mongo_id || data.record_id || "Saved";
  await loadHistory();
}

async function runSimulation() {
  const features = readFeatures();
  const rainfall_delta = Number(document.getElementById("rainfallDelta").value || 0);
  const humidity_delta = Number(document.getElementById("humidityDelta").value || 0);
  const temperature_delta = Number(document.getElementById("temperatureDelta").value || 0);

  const data = await api("/simulate", "POST", {
    features,
    rainfall_delta,
    humidity_delta,
    temperature_delta,
  });

  renderResult("Simulation", data);
  latestRecord.textContent = data.mongo_id || data.record_id || "Saved";
  await loadHistory();
}

async function loadHistory() {
  const data = await api("/history");
  const records = data.records || [];

  if (!records.length) {
    historyList.innerHTML = '<div class="history-empty">No records yet.</div>';
    renderCharts([]);
    return;
  }

  historyList.innerHTML = records.slice(0, 10).map((record, index) => {
    const risk = record.simulated_risk ? `${record.real_risk} → ${record.simulated_risk}` : record.predicted_risk;
    return `
      <article class="history-item">
        <div>
          <p class="history-index">Record ${index + 1}</p>
          <strong>${risk}</strong>
        </div>
        <div class="history-meta">
          <span>${formatValue(record.city || record.type || "Unknown")}</span>
          <span>${formatValue(record.timestamp || "")}</span>
        </div>
      </article>
    `;
  }).join("");

  const hasHighRisk = records.some((record) =>
    String(record.predicted_risk || "").toLowerCase() === "high" ||
    String(record.real_risk || "").toLowerCase() === "high" ||
    String(record.simulated_risk || "").toLowerCase() === "high"
  );

  if (hasHighRisk) {
    updateRiskAlert("high", "History");
    updateSolutionsLink("High");
  }

  renderCharts(records);
}

function wire(id, handler) {
  document.getElementById(id).addEventListener("click", async () => {
    try {
      await handler();
    } catch (error) {
      resultEmpty.classList.add("hidden");
      resultCard.classList.remove("hidden");
      updateRiskAlert(null, "");
      resultCard.innerHTML = `<div class="error-box">${formatValue(error.message || error)}</div>`;
    }
  });
}

wire("predictBtn", runPrediction);
wire("simulateBtn", runSimulation);
wire("loadHistoryBtn", loadHistory);

loadHealth();
loadSchema().catch((error) => {
  schemaNotice.textContent = error.message || "Unable to load schema.";
  setStatus(schemaStatus, "Unavailable", "bad");
});
loadHistory().catch(() => {
  historyList.innerHTML = '<div class="history-empty">Unable to load history.</div>';
});
