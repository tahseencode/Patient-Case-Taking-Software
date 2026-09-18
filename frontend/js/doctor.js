/**
 * MediKiosk AI & AyurKiosk - Physician OPD Consultation Desk Engine
 * SIH26047: AI-Powered Digital Clinical Intake & AYUSH OPD Platform
 */

const doctorModule = (() => {
  let activeSessionId = null;
  let currentPatientData = null;
  let queueList = [];
  let prescriptionsList = [];

  function init() {
    setupEventListeners();
    refreshQueue();
    // Default mock prescription items
    prescriptionsList = [
      {
        medicine_name: "Tab Telma-H (Telmisartan 40mg + HCTZ 12.5mg)",
        dosage: "40mg",
        frequency: "1-0-0",
        duration: "30 days",
        instructions: "Morning after breakfast"
      },
      {
        medicine_name: "Tab Glycomet-GP 2 (Metformin 500mg + Glimepiride 2mg)",
        dosage: "500mg/2mg",
        frequency: "1-0-1",
        duration: "30 days",
        instructions: "Before meals"
      }
    ];
  }

  function setupEventListeners() {
    // Add Prescription Item Button
    const addRxBtn = document.getElementById("doctorAddRxBtn");
    if (addRxBtn) {
      addRxBtn.addEventListener("click", () => {
        addPrescriptionRow({
          medicine_name: "Tab Ecosprin 75mg",
          dosage: "75mg",
          frequency: "0-1-0",
          duration: "30 days",
          instructions: "After lunch"
        });
      });
    }

    // Complete Consultation & ABDM Sync Button
    const completeConsultBtn = document.getElementById("completeConsultBtn");
    if (completeConsultBtn) {
      completeConsultBtn.addEventListener("click", completeConsultation);
    }

    // Save Physician Notes Button
    const saveNotesBtn = document.getElementById("saveDoctorNotesBtn");
    if (saveNotesBtn) {
      saveNotesBtn.addEventListener("click", updateDoctorNotes);
    }
  }

  // Refresh OPD Queue
  async function refreshQueue() {
    try {
      const res = await fetch(`${API_BASE}/doctor/opd-queue`);
      const data = await res.json();
      if (data.success) {
        queueList = data.queue;
        renderQueueList(queueList);
        document.getElementById("opdQueueCount").textContent = `${data.total_waiting} Waiting`;
        
        // Auto-select first patient if none selected
        if (!activeSessionId && queueList.length > 0) {
          loadPatientCase(queueList[0].session_id);
        }
      }
    } catch (err) {
      console.error("Failed to fetch OPD queue", err);
    }
  }

  function renderQueueList(queue) {
    const listContainer = document.getElementById("opdQueueItems");
    if (!listContainer) return;
    listContainer.innerHTML = "";

    if (queue.length === 0) {
      listContainer.innerHTML = `
        <div style="text-align:center;padding:30px;color:var(--text-muted);font-size:0.9rem;">
          No patients waiting in OPD queue.
        </div>
      `;
      return;
    }

    queue.forEach(item => {
      const card = document.createElement("div");
      const triageClass = item.triage_level === "emergency" ? "emergency-border" : item.triage_level === "priority" ? "priority-border" : "routine-border";
      card.className = `queue-item-card ${triageClass} ${activeSessionId === item.session_id ? 'active' : ''}`;
      card.setAttribute("data-session-id", item.session_id);
      
      card.innerHTML = `
        <div class="queue-top-row">
          <span class="queue-token-badge">${item.token}</span>
          <span class="queue-wait-badge">⏱️ ~${item.waiting_minutes || 5} min</span>
        </div>
        <div class="queue-patient-name">${item.patient_name}, ${item.age}y/${item.gender ? item.gender[0] : 'M'}</div>
        <div class="queue-complaint-preview">🩺 ${item.chief_complaint || 'General OPD Consultation'}</div>
        <div style="display:flex;justify-content:space-between;align-items:center;margin-top:4px;">
          <span class="abdm-badge" style="font-size:0.65rem;">${item.stream === 'ayush' ? '🌿 AYUSH' : '💊 ALLOPATHY'}</span>
          ${item.is_red_flag ? '<span class="pulse-badge" style="font-size:0.65rem;">RED-FLAG</span>' : ''}
        </div>
      `;

      card.addEventListener("click", () => {
        loadPatientCase(item.session_id);
      });

      listContainer.appendChild(card);
    });
  }

  // Load Patient Deep Case View
  async function loadPatientCase(sessionId) {
    activeSessionId = sessionId;
    
    // Highlight selected queue card
    document.querySelectorAll(".queue-item-card").forEach(c => {
      c.classList.toggle("active", c.getAttribute("data-session-id") === sessionId);
    });

    try {
      const res = await fetch(`${API_BASE}/doctor/patient-summary/${sessionId}`);
      const data = await res.json();
      if (data.success) {
        currentPatientData = data;
        renderPatientWorkspace(data);
      }
    } catch (err) {
      console.error(err);
      window.app.showToast("Failed to load patient case record", "error");
    }
  }

  function renderPatientWorkspace(data) {
    const pat = data.patient;
    const sum = data.summary;
    const triage = data.triage;
    const ayush = data.ayush;

    // Header Demographics
    document.getElementById("docPatientName").textContent = pat.name;
    document.getElementById("docPatientMeta").textContent = `${pat.age} Years / ${pat.gender} | Token: ${pat.token_number} | Phone: ${pat.phone}`;
    document.getElementById("docPatientAbha").textContent = pat.abha_id || pat.abha_number || "ABHA-KYC-PENDING";

    // Triage Badge
    const triageBadge = document.getElementById("docTriageBadge");
    if (triageBadge) {
      if (triage && triage.is_red_flag) {
        triageBadge.className = "pulse-badge";
        triageBadge.textContent = "EMERGENCY TRIAGE RED-FLAG";
        triageBadge.style.display = "inline-block";
      } else {
        triageBadge.className = "dpdp-badge";
        triageBadge.textContent = "ROUTINE OPD";
        triageBadge.style.display = "inline-block";
      }
    }

    // AI Synthesized Clinical Summary
    if (sum) {
      document.getElementById("docChiefComplaint").textContent = sum.chief_complaint;
      document.getElementById("docHpiNarrative").textContent = sum.history_of_present_illness;

      // Past Medical History Tags
      const pastHistContainer = document.getElementById("docPastHistoryTags");
      pastHistContainer.innerHTML = "";
      (sum.past_medical_history || []).forEach(h => {
        pastHistContainer.innerHTML += `<span class="tag-item">🩺 ${h}</span>`;
      });

      // Allergies
      const allergyContainer = document.getElementById("docAllergiesTags");
      allergyContainer.innerHTML = "";
      (sum.drug_allergies || ["NKDA"]).forEach(a => {
        allergyContainer.innerHTML += `<span class="tag-item allergy">⚠️ ${a}</span>`;
      });

      // Reconciled Medications
      const medsContainer = document.getElementById("docReconciledMeds");
      medsContainer.innerHTML = "";
      if (sum.current_medications && sum.current_medications.length > 0) {
        sum.current_medications.forEach(m => {
          medsContainer.innerHTML += `
            <div class="extracted-item-pill">
              <span>💊 <strong>${m.drug_name}</strong> (${m.strength || ''}) - ${m.dosage_frequency}</span>
              <span style="font-size:0.75rem;color:var(--text-muted);">${m.timing}</span>
            </div>
          `;
        });
      } else {
        medsContainer.innerHTML = `<span style="font-size:0.8rem;color:var(--text-muted);">No current active medications extracted.</span>`;
      }

      // Abnormal Lab Investigations
      const labContainer = document.getElementById("docInvestigationBadges");
      labContainer.innerHTML = "";
      if (sum.investigation_summary && sum.investigation_summary.length > 0) {
        sum.investigation_summary.forEach(inv => {
          const flagClass = inv.flag === "CRITICAL" ? "critical" : inv.flag === "HIGH" ? "high" : "normal";
          labContainer.innerHTML += `
            <div class="extracted-item-pill">
              <span>🧪 <strong>${inv.test_name}</strong>: ${inv.measured_value} ${inv.unit}</span>
              <span class="flag-badge ${flagClass}">${inv.flag} (${inv.reference_range})</span>
            </div>
          `;
        });
      } else {
        labContainer.innerHTML = `<span style="font-size:0.8rem;color:var(--text-muted);">No lab test reports attached.</span>`;
      }

      // Suggested ICD-10 and NAMASTE Codes
      const icdContainer = document.getElementById("docIcdSuggestions");
      icdContainer.innerHTML = "";
      (sum.icd10_suggestions || []).forEach(code => {
        const chip = document.createElement("div");
        chip.className = "code-suggestion-chip";
        chip.innerHTML = `<span>+ ${code.code}: ${code.title}</span>`;
        chip.addEventListener("click", () => {
          document.getElementById("docDiagnosisInput").value = `${code.code} - ${code.title}`;
          window.app.showToast(`Applied ICD-10 Code: ${code.code}`, "info");
        });
        icdContainer.appendChild(chip);
      });

      // NAMASTE AYUSH Codes
      (sum.namaste_suggestions || []).forEach(code => {
        const chip = document.createElement("div");
        chip.className = "code-suggestion-chip namaste";
        chip.innerHTML = `<span>🌿 ${code.code}: ${code.title}</span>`;
        chip.addEventListener("click", () => {
          document.getElementById("docDiagnosisInput").value = `${code.code} - ${code.title}`;
          window.app.showToast(`Applied NAMASTE AYUSH Code: ${code.code}`, "info");
        });
        icdContainer.appendChild(chip);
      });
    }

    // AYUSH Panel Toggle & Render
    const ayushPanel = document.getElementById("docAyushAssessmentPanel");
    if (ayush && pat.stream === "ayush") {
      ayushPanel.style.display = "block";
      document.getElementById("docAyushPrakriti").textContent = ayush.dominant_prakriti;
      document.getElementById("docAyushAgni").textContent = ayush.agni;
      document.getElementById("docAyushKoshtha").textContent = ayush.koshtha;
      document.getElementById("docAyushNidana").textContent = (ayush.nidana_causative_factors || []).join("; ") || "Ahara-Vihara imbalances";
    } else {
      ayushPanel.style.display = "none";
    }

    // Render Prescription Builder Table
    renderPrescriptionsTable();
  }

  function renderPrescriptionsTable() {
    const tbody = document.getElementById("doctorPrescriptionTbody");
    if (!tbody) return;
    tbody.innerHTML = "";

    prescriptionsList.forEach((item, idx) => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td><input type="text" class="form-input" style="padding:6px 8px;font-size:0.85rem;" value="${item.medicine_name}" data-idx="${idx}" data-field="medicine_name"></td>
        <td><input type="text" class="form-input" style="padding:6px 8px;font-size:0.85rem;width:80px;" value="${item.dosage}" data-idx="${idx}" data-field="dosage"></td>
        <td><input type="text" class="form-input" style="padding:6px 8px;font-size:0.85rem;width:80px;" value="${item.frequency}" data-idx="${idx}" data-field="frequency"></td>
        <td><input type="text" class="form-input" style="padding:6px 8px;font-size:0.85rem;width:90px;" value="${item.duration}" data-idx="${idx}" data-field="duration"></td>
        <td><input type="text" class="form-input" style="padding:6px 8px;font-size:0.85rem;" value="${item.instructions}" data-idx="${idx}" data-field="instructions"></td>
        <td><button type="button" class="btn btn-danger btn-sm" onclick="window.doctorModule.removeRx(${idx})">✕</button></td>
      `;
      tbody.appendChild(row);
    });

    // Attach row change listeners
    tbody.querySelectorAll("input").forEach(inp => {
      inp.addEventListener("change", (e) => {
        const idx = parseInt(e.target.getAttribute("data-idx"));
        const field = e.target.getAttribute("data-field");
        if (prescriptionsList[idx]) {
          prescriptionsList[idx][field] = e.target.value;
        }
      });
    });
  }

  function addPrescriptionRow(item) {
    prescriptionsList.push(item);
    renderPrescriptionsTable();
  }

  function removeRx(index) {
    prescriptionsList.splice(index, 1);
    renderPrescriptionsTable();
  }

  // Save Doctor Clinical Notes
  async function updateDoctorNotes() {
    if (!activeSessionId) return;
    const notes = document.getElementById("docClinicalNotesInput").value.trim();

    try {
      const res = await fetch(`${API_BASE}/doctor/update-summary`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: activeSessionId,
          physician_notes: notes
        })
      });
      const data = await res.json();
      if (data.success) {
        window.app.showToast("Physician notes saved successfully", "success");
      }
    } catch (err) {
      console.error(err);
    }
  }

  // Complete Consultation & ABDM FHIR Push
  async function completeConsultation() {
    if (!activeSessionId) {
      window.app.showToast("No active patient selected", "error");
      return;
    }

    const diagnosis = document.getElementById("docDiagnosisInput").value.trim() || "Type 2 Diabetes Mellitus with Essential Hypertension";
    const notes = document.getElementById("docClinicalNotesInput").value.trim() || "Patient evaluated and stabilized. Strict dietary compliance and exercise routine advised.";

    const payload = {
      session_id: activeSessionId,
      doctor_name: "Dr. S. K. Mukherjee, MD",
      doctor_department: "General Medicine / OPD Room 104",
      diagnosis: diagnosis,
      clinical_notes: notes,
      prescriptions: prescriptionsList,
      ordered_investigations: ["Repeat HbA1c in 3 months", "Serum Electrolytes & Creatinine", "Resting 12-Lead ECG"],
      follow_up_date: "After 2 weeks"
    };

    try {
      const res = await fetch(`${API_BASE}/doctor/prescribe-and-complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success) {
        window.app.showToast("Consultation Completed & ABDM FHIR R4 Bundle Generated!", "success");
        
        // Refresh queue
        refreshQueue();

        // Switch to FHIR Hub view to display the generated ABDM record
        setTimeout(() => {
          window.app.switchRole("fhir");
          if (window.fhirModule) {
            window.fhirModule.loadFhirBundle(activeSessionId);
          }
        }, 500);
      }
    } catch (err) {
      console.error(err);
      window.app.showToast("Error completing consultation", "error");
    }
  }

  return {
    init,
    refreshQueue,
    loadPatientCase,
    removeRx,
    activeSessionId
  };
})();

window.doctorModule = doctorModule;
