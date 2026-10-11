/**
 * MediKiosk AI & AyurKiosk - ABDM FHIR R4 & DPDP 2023 Compliance Engine
 * SIH26047: AI-Powered Digital Clinical Intake & AYUSH OPD Platform
 */

const fhirModule = (() => {
  let currentBundle = null;
  let currentSessionId = "SESS-101";

  function init() {
    setupEventListeners();
    loadFhirBundle(currentSessionId);
  }

  function setupEventListeners() {
    // Copy FHIR JSON Button
    const copyBtn = document.getElementById("copyFhirJsonBtn");
    if (copyBtn) {
      copyBtn.addEventListener("click", () => {
        if (!currentBundle) return;
        navigator.clipboard.writeText(JSON.stringify(currentBundle, null, 2));
        window.app.showToast("FHIR R4 Bundle copied to clipboard!", "success");
      });
    }

    // Push to ABDM HIE-CM Network Simulation Button
    const pushAbdmBtn = document.getElementById("pushAbdmHieBtn");
    if (pushAbdmBtn) {
      pushAbdmBtn.addEventListener("click", simulateAbdmPush);
    }

    // View DPDP Audit Certificate Button
    const dpdpAuditBtn = document.getElementById("viewDpdpAuditBtn");
    if (dpdpAuditBtn) {
      dpdpAuditBtn.addEventListener("click", showDpdpCertificateModal);
    }
  }

  async function loadFhirBundle(sessionId = "SESS-101") {
    currentSessionId = sessionId;
    try {
      const res = await fetch(`${API_BASE}/abdm/fhir-bundle/${sessionId}`);
      const data = await res.json();
      if (data.success && data.bundle) {
        currentBundle = data.bundle;
        renderFhirTree(data.bundle);
        renderJsonCode(data.bundle);
      }
    } catch (err) {
      console.error("Failed to fetch FHIR bundle", err);
    }
  }

  function renderFhirTree(bundle) {
    const list = document.getElementById("fhirResourceList");
    if (!list) return;
    list.innerHTML = "";

    const entries = bundle.entry || [];
    document.getElementById("fhirTotalEntriesCount").textContent = `${entries.length} Resources`;

    entries.forEach((entry, idx) => {
      const res = entry.resource;
      const card = document.createElement("div");
      card.className = "sample-doc-item";
      card.style.marginBottom = "8px";
      
      let resDesc = "";
      if (res.resourceType === "Composition") resDesc = res.title || "Clinical Intake Document";
      else if (res.resourceType === "Patient") resDesc = `Patient: ${res.name?.[0]?.text || 'Ramesh Kumar'}`;
      else if (res.resourceType === "Condition") resDesc = res.code?.coding?.[0]?.display || "Clinical Diagnosis";
      else if (res.resourceType === "MedicationRequest") resDesc = res.medicationCodeableConcept?.coding?.[0]?.display || "Prescription Item";
      else if (res.resourceType === "Consent") resDesc = "DPDP Act 2023 Digital Consent";
      else resDesc = `${res.resourceType} Record`;

      card.innerHTML = `
        <div>
          <div class="doc-title"><span class="abdm-badge" style="font-size:0.7rem;">${res.resourceType}</span> ${resDesc}</div>
          <div class="doc-meta">ID: ${res.id || `urn:uuid:${idx}`} | Standard: HL7 FHIR R4</div>
        </div>
        <button type="button" class="btn btn-secondary btn-sm" onclick="window.fhirModule.inspectResource(${idx})">Inspect</button>
      `;

      list.appendChild(card);
    });
  }

  function renderJsonCode(bundle) {
    const box = document.getElementById("fhirJsonViewerCode");
    if (box) {
      box.textContent = JSON.stringify(bundle, null, 2);
    }
  }

  function inspectResource(idx) {
    if (!currentBundle || !currentBundle.entry || !currentBundle.entry[idx]) return;
    const res = currentBundle.entry[idx].resource;
    renderJsonCode(res);
    window.app.showToast(`Inspecting ${res.resourceType} Resource`, "info");
  }

  function refreshCurrentBundle() {
    loadFhirBundle(currentSessionId);
  }

  function simulateAbdmPush() {
    window.app.showToast("Initiating cryptographic transmission to ABDM HIE-CM Gateway...", "info");
    setTimeout(() => {
      window.app.showToast("ABDM Status 200 OK: FHIR Bundle successfully synced to Patient Health Record (PHR)!", "success");
    }, 1200);
  }

  async function showDpdpCertificateModal() {
    try {
      const res = await fetch(`${API_BASE}/abdm/dpdp-audit/${currentSessionId}`);
      const data = await res.json();
      if (data.success) {
        const modal = document.getElementById("dpdpModal");
        const hashElem = document.getElementById("dpdpCertHash");
        const timeElem = document.getElementById("dpdpCertTime");
        const patElem = document.getElementById("dpdpCertPatient");
        
        if (hashElem) hashElem.textContent = data.consent.consent_hash || "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08";
        if (timeElem) timeElem.textContent = data.consent.timestamp;
        if (patElem) patElem.textContent = `Patient ID: ${data.consent.patient_id}`;
        
        if (modal) modal.classList.add("active");
      }
    } catch (err) {
      console.error(err);
    }
  }

  return {
    init,
    loadFhirBundle,
    refreshCurrentBundle,
    inspectResource
  };
})();

window.fhirModule = fhirModule;
