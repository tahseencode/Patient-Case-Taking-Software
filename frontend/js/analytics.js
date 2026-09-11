/**
 * MediKiosk AI & AyurKiosk - Hospital OPD Analytics Engine
 * SIH26047: AI-Powered Digital Clinical Intake & AYUSH OPD Platform
 */

const analyticsModule = (() => {
  function init() {
    loadMetrics();
    const refreshBtn = document.getElementById("refreshAnalyticsBtn");
    if (refreshBtn) {
      refreshBtn.addEventListener("click", loadMetrics);
    }
  }

  async function loadMetrics() {
    try {
      const res = await fetch(`${API_BASE}/abdm/hospital-stats`);
      const data = await res.json();
      if (data.success && data.metrics) {
        renderMetrics(data.metrics);
      }
    } catch (err) {
      console.error("Failed to load hospital stats", err);
    }
  }

  function renderMetrics(m) {
    // Stat Metrics
    const timeSavedElem = document.getElementById("statTimeSavedPct");
    const intakeVolElem = document.getElementById("statDailyIntakeVolume");
    const redFlagsElem = document.getElementById("statRedFlagsCount");
    const docsDigitizedElem = document.getElementById("statDocsDigitized");
    const fhirPushedElem = document.getElementById("statFhirBundlesPushed");

    if (timeSavedElem) timeSavedElem.textContent = `${m.clinical_time_saved_percentage}%`;
    if (intakeVolElem) intakeVolElem.textContent = m.daily_opd_intake_volume.toLocaleString();
    if (redFlagsElem) redFlagsElem.textContent = m.emergency_red_flags_intercepted;
    if (docsDigitizedElem) docsDigitizedElem.textContent = m.scanned_documents_digitized.toLocaleString();
    if (fhirPushedElem) fhirPushedElem.textContent = m.abdm_fhir_bundles_pushed.toLocaleString();

    // Time Comparison Metric
    const intakeTimeElem = document.getElementById("statPreConsultTime");
    const baselineTimeElem = document.getElementById("statBaselineTime");
    if (intakeTimeElem) intakeTimeElem.textContent = `${m.average_pre_consultation_time_sec}s`;
    if (baselineTimeElem) baselineTimeElem.textContent = `${m.previous_baseline_history_time_sec}s`;
  }

  return {
    init,
    loadMetrics
  };
})();

window.analyticsModule = analyticsModule;
