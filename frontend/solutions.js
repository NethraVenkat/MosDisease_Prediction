const riskSelect = document.getElementById("riskSelect");
const showSolutionsBtn = document.getElementById("showSolutionsBtn");
const solutionCards = document.getElementById("solutionCards");
const riskSummary = document.getElementById("riskSummary");
const timeRecommendation = document.getElementById("timeRecommendation");
const healthAdvisoryList = document.getElementById("healthAdvisoryList");
const alertSimulation = document.getElementById("alertSimulation");

const SOLUTIONS = {
  Low: {
    className: "low",
    icon: "\u2705",
    title: "Low Risk Prevention",
    tips: [
      "Maintain cleanliness in homes and nearby surroundings.",
      "Avoid stagnant water in containers, tires, and gutters.",
      "Continue routine monitoring of mosquito-prone areas.",
      "Inspect water storage tanks weekly and keep them covered.",
      "Encourage households to follow a fixed community cleanup schedule.",
      "Promote early symptom awareness and prompt reporting in clinics.",
    ],
    timeRecommendation: "\u2705 Low immediate risk. Maintain preventive measures.",
    alertSimulation: "No alert required.",
  },
  Medium: {
    className: "medium",
    icon: "\u26A0\uFE0F",
    title: "Medium Risk Actions",
    tips: [
      "Use mosquito repellents and protective clothing.",
      "Run community awareness campaigns for early prevention.",
      "Increase local area inspections and vector control drives.",
      "Organize neighborhood fogging in recurring hotspot streets.",
      "Deploy larvicide treatment in drains and standing water zones.",
      "Coordinate schools and public spaces for preventive messaging.",
    ],
    timeRecommendation: "\u26A0\uFE0F Monitor conditions over the next 2 weeks.",
    alertSimulation: "\uD83D\uDCE9 Advisory notification may be sent.",
  },
  High: {
    className: "high",
    icon: "\uD83D\uDEA8",
    title: "High Risk Emergency Response",
    tips: [
      "Immediate sanitation actions in high-risk zones.",
      "Trigger government intervention and rapid response teams.",
      "Issue medical alerts and prepare healthcare support.",
      "Activate emergency surveillance with daily case tracking.",
      "Scale hospital triage capacity and stock critical supplies.",
      "Launch targeted door-to-door health checks in hotspot blocks.",
      "Set up temporary public helplines for symptoms and referrals.",
    ],
    timeRecommendation: "\uD83D\uDEA8 Next 7 days are critical. Take immediate action!",
    alertSimulation: "\uD83D\uDCE9 SMS Alert would be triggered for this region.",
  },
};

const HEALTH_ADVISORY_SYMPTOMS = {
  Low: ["Normal"],
  Medium: ["Fever", "Cold", "Headache"],
  High: ["High fever", "Severe headache", "Joint pain", "Fatigue", "Nausea"],
};

function normalizeRisk(value) {
  if (!value) return "Low";
  const text = String(value).toLowerCase();
  if (text === "high") return "High";
  if (text === "medium") return "Medium";
  return "Low";
}

function getRiskFromContext() {
  const queryRisk = new URLSearchParams(window.location.search).get("risk");
  if (queryRisk) return normalizeRisk(queryRisk);

  const savedRisk = window.localStorage.getItem("predictedRisk");
  if (savedRisk) return normalizeRisk(savedRisk);

  return "Low";
}

function renderHealthAdvisory(level) {
  const symptoms = HEALTH_ADVISORY_SYMPTOMS[level] || HEALTH_ADVISORY_SYMPTOMS.Low;
  healthAdvisoryList.innerHTML = symptoms
    .map((symptom) => `<li>${symptom}</li>`)
    .join("");
}

function renderSolutions(level) {
  const info = SOLUTIONS[level];
  if (!info) {
    solutionCards.innerHTML = '<p class="empty-note">Select a risk level to view solutions.</p>';
    return;
  }

  riskSummary.innerHTML = `Current selected risk level: <strong>${level}</strong>`;
  timeRecommendation.textContent = info.timeRecommendation;
  alertSimulation.textContent = info.alertSimulation;
  renderHealthAdvisory(level);

  solutionCards.innerHTML = `
    <article class="solution-card ${info.className}">
      <h3>${info.icon} ${info.title}</h3>
      <ul>
        ${info.tips.map((tip) => `<li>${tip}</li>`).join("")}
      </ul>
    </article>
  `;
}

showSolutionsBtn.addEventListener("click", () => {
  const level = normalizeRisk(riskSelect.value);
  riskSelect.value = level;
  window.localStorage.setItem("predictedRisk", level);
  renderSolutions(level);
});

riskSelect.addEventListener("change", () => {
  const level = normalizeRisk(riskSelect.value);
  riskSelect.value = level;
  window.localStorage.setItem("predictedRisk", level);
  renderSolutions(level);
});

const initialRisk = getRiskFromContext();
riskSelect.value = initialRisk;
renderSolutions(initialRisk);
