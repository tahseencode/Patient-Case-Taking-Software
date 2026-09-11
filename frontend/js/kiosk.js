/**
 * MediKiosk AI & AyurKiosk - Patient Kiosk Intake Engine
 * SIH26047: AI-Powered Digital Clinical Intake & AYUSH OPD Platform
 */

const kioskModule = (() => {
  let currentStep = 1;
  const totalSteps = 6;
  
  let currentSessionData = {
    sessionId: null,
    patientId: null,
    tokenNumber: null,
    stream: "allopathy",
    language: "hi",
    chiefComplaintId: "chest_pain",
    chiefComplaintTitle: "Chest Pain / Discomfort",
    affectedBodyPart: "chest",
    socrates: {
      site: "Left Side of Chest",
      onset: "2 to 5 days ago",
      character: "Heavy Pressure / Squeezing / Tightness",
      radiation: "Spreads to Left Arm, Shoulder or Jaw",
      associations: ["Profuse Cold Sweating", "Breathlessness / Dyspnea"],
      timing: "Continuous / Constant",
      exacerbating_factors: ["Physical Exertion (Walking/Stairs)"],
      relieving_factors: ["Sublingual Nitrate / Rest"],
      severity_score: 8
    },
    ayushAnswers: {},
    ayushResult: null,
    uploadedDocuments: [],
    triageResult: null,
    summary: null
  };

  let allComplaints = [];
  let socratesStepIndex = 0;
  const socratesStepsTotal = 8;

  function init() {
    setupEventListeners();
    loadChiefComplaints();
    loadSampleDocuments();
    updateStepperUI();
  }

  function setupEventListeners() {
    // ABHA Verification
    const verifyAbhaBtn = document.getElementById("verifyAbhaBtn");
    if (verifyAbhaBtn) {
      verifyAbhaBtn.addEventListener("click", handleAbhaVerification);
    }

    // Stream Selector Buttons
    document.querySelectorAll(".stream-option-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".stream-option-btn").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        currentSessionData.stream = btn.getAttribute("data-stream");
        
        // Toggle Step 4 AYUSH indicator in Stepper
        const step4Nav = document.querySelector('.kiosk-step-item[data-step="4"]');
        if (step4Nav) {
          step4Nav.style.display = currentSessionData.stream === "ayush" ? "flex" : "none";
        }
      });
    });

    // Body Map Pill Selectors
    document.querySelectorAll(".body-pill-btn").forEach(pill => {
      pill.addEventListener("click", () => {
        document.querySelectorAll(".body-pill-btn").forEach(p => p.classList.remove("active"));
        pill.classList.add("active");
        const region = pill.getAttribute("data-region");
        selectBodyRegion(region);
      });
    });

    // SVG Body Region Targets
    document.querySelectorAll(".body-region-target").forEach(elem => {
      elem.addEventListener("click", () => {
        const region = elem.getAttribute("data-region");
        selectBodyRegion(region);
        
        // Update pill active
        document.querySelectorAll(".body-pill-btn").forEach(p => {
          p.classList.toggle("active", p.getAttribute("data-region") === region);
        });
      });
    });

    // Voice Mic Button
    const voiceMicBtn = document.getElementById("voiceMicBtn");
    if (voiceMicBtn) {
      voiceMicBtn.addEventListener("click", () => {
        window.app.toggleVoiceRecording(currentSessionData.chiefComplaintId);
      });
    }

    // Pain Severity Slider
    const severitySlider = document.getElementById("severitySlider");
    if (severitySlider) {
      severitySlider.addEventListener("input", (e) => {
        const val = parseInt(e.target.value);
        currentSessionData.socrates.severity_score = val;
        updateSeverityUI(val);
      });
    }

    // Next / Prev Step Navigation Buttons
    const nextBtn = document.getElementById("kioskNextBtn");
    const prevBtn = document.getElementById("kioskPrevBtn");
    if (nextBtn) nextBtn.addEventListener("click", goToNextStep);
    if (prevBtn) prevBtn.addEventListener("click", goToPrevStep);

    // Stepper Sidebar Clicks
    document.querySelectorAll(".kiosk-step-item").forEach(item => {
      item.addEventListener("click", () => {
        const step = parseInt(item.getAttribute("data-step"));
        if (step <= currentStep || currentSessionData.sessionId) {
          navigateToStep(step);
        }
      });
    });

    // Custom Document OCR Process Button
    const processCustomDocBtn = document.getElementById("processCustomDocBtn");
    if (processCustomDocBtn) {
      processCustomDocBtn.addEventListener("click", handleCustomDocumentUpload);
    }
  }

  function updateSeverityUI(val) {
    const badge = document.getElementById("severityScoreBadge");
    const emoji = document.getElementById("severityEmoji");
    if (badge) badge.textContent = `${val}/10`;
    if (emoji) {
      if (val <= 3) emoji.textContent = "😊";
      else if (val <= 6) emoji.textContent = "😐";
      else if (val <= 8) emoji.textContent = "😣";
      else emoji.textContent = "😫";
    }
  }

  // Step 1: ABHA Verification & Session Creation
  async function handleAbhaVerification() {
    const input = document.getElementById("patientAbhaInput").value.trim();
    if (!input) {
      window.app.showToast("Please enter an ABHA ID, 14-digit ABHA Number, or Mobile number", "error");
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/abdm/verify-abha`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ abha_input: input })
      });
      const data = await res.json();
      if (data.success) {
        document.getElementById("patientAbhaInput").value = data.abha_id;
        document.getElementById("abhaVerifyStatus").innerHTML = `
          <span style="color:var(--triage-green);font-weight:600;font-size:0.8rem;">
            ✓ ${data.message} (Number: ${data.abha_number})
          </span>
        `;
        window.app.showToast(`ABHA Verified: ${data.abha_id}`, "success");
      }
    } catch (err) {
      console.error(err);
      window.app.showToast("ABHA verification error, continuing in local mode.", "info");
    }
  }

  async function startIntakeSession() {
    const name = document.getElementById("patientNameInput").value.trim() || "Ramesh Kumar";
    const age = parseInt(document.getElementById("patientAgeInput").value) || 58;
    const gender = document.getElementById("patientGenderSelect").value || "Male";
    const phone = document.getElementById("patientPhoneInput").value.trim() || "9876543210";
    const abhaId = document.getElementById("patientAbhaInput").value.trim() || "ramesh.kumar58@abdm";

    const payload = {
      name,
      age,
      gender,
      phone,
      abha_id: abhaId,
      language: window.app.appState.currentLanguage,
      stream: currentSessionData.stream,
      voice_consent: document.getElementById("consentVoiceCheck")?.checked ?? true,
      ocr_consent: document.getElementById("consentOcrCheck")?.checked ?? true,
      abha_consent: document.getElementById("consentAbhaCheck")?.checked ?? true
    };

    try {
      const res = await fetch(`${API_BASE}/kiosk/start-session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();
      if (data.success) {
        currentSessionData.sessionId = data.session_id;
        currentSessionData.patientId = data.patient.patient_id;
        currentSessionData.tokenNumber = data.token_number;
        window.app.appState.currentSession = data;
        return true;
      }
    } catch (err) {
      console.error(err);
    }
    return false;
  }

  // Step 2: Body Map & Chief Complaints
  async function loadChiefComplaints() {
    try {
      const res = await fetch(`${API_BASE}/kiosk/complaints?language=${window.app.appState.currentLanguage}`);
      const data = await res.json();
      if (data.success) {
        allComplaints = data.complaints;
        renderComplaintsGrid(allComplaints);
      }
    } catch (err) {
      console.error("Failed to load chief complaints", err);
    }
  }

  function selectBodyRegion(region) {
    currentSessionData.affectedBodyPart = region;
    
    // Highlight SVG region
    document.querySelectorAll(".body-region-target").forEach(elem => {
      elem.classList.toggle("active", elem.getAttribute("data-region") === region);
    });

    // Filter complaints
    if (region === "all" || region === "whole_body") {
      renderComplaintsGrid(allComplaints);
    } else {
      const filtered = allComplaints.filter(c => c.body_part === region || c.body_part === "whole_body");
      renderComplaintsGrid(filtered.length > 0 ? filtered : allComplaints);
    }
  }

  function renderComplaintsGrid(complaints) {
    const grid = document.getElementById("complaintsGrid");
    if (!grid) return;
    grid.innerHTML = "";

    complaints.forEach(item => {
      const card = document.createElement("div");
      card.className = `complaint-card ${currentSessionData.chiefComplaintId === item.id ? 'active' : ''}`;
      card.innerHTML = `
        <div class="title-row">
          <span>${item.name_en}</span>
          ${item.is_high_risk ? '<span class="high-risk-indicator" title="Red-Flag Triage Monitored"></span>' : ''}
        </div>
        <div class="vernacular-name">${item[`name_${window.app.appState.currentLanguage}`] || item.name_hi || ''}</div>
        <div class="specialty-tag">🏥 ${item.specialty}</div>
      `;
      card.addEventListener("click", () => {
        document.querySelectorAll(".complaint-card").forEach(c => c.classList.remove("active"));
        card.classList.add("active");
        currentSessionData.chiefComplaintId = item.id;
        currentSessionData.chiefComplaintTitle = item.name_en;
        currentSessionData.affectedBodyPart = item.body_part;
      });
      grid.appendChild(card);
    });
  }

  // Voice Transcript Parsing & Natural Language Symptom Extractor
  async function handleVoiceInput(transcript) {
    try {
      const res = await fetch(`${API_BASE}/kiosk/parse-voice`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          transcript,
          chief_complaint_id: currentSessionData.chiefComplaintId,
          language: window.app.appState.currentLanguage
        })
      });
      const data = await res.json();
      if (data.success && data.extracted) {
        const ext = data.extracted;
        if (ext.onset) currentSessionData.socrates.onset = ext.onset;
        if (ext.character) currentSessionData.socrates.character = ext.character;
        if (ext.radiation) currentSessionData.socrates.radiation = ext.radiation;
        if (ext.associations && ext.associations.length > 0) {
          currentSessionData.socrates.associations = ext.associations;
        }
        if (ext.severity_score) {
          currentSessionData.socrates.severity_score = ext.severity_score;
          const slider = document.getElementById("severitySlider");
          if (slider) slider.value = ext.severity_score;
          updateSeverityUI(ext.severity_score);
        }
        window.app.showToast("Voice symptoms processed & matched to SOCRATES profile!", "success");
        renderSocratesInteractiveStep();
      }
    } catch (err) {
      console.error(err);
    }
  }

  // Step 3: SOCRATES Guided Questioning
  async function renderSocratesInteractiveStep() {
    try {
      const res = await fetch(`${API_BASE}/kiosk/socrates-step?step=${socratesStepIndex}&language=${window.app.appState.currentLanguage}`);
      const data = await res.json();
      if (data.success && data.data) {
        const step = data.data;
        document.getElementById("socratesStepNum").textContent = `Step ${socratesStepIndex + 1} of ${socratesStepsTotal}`;
        document.getElementById("socratesFieldBadge").textContent = `SOCRATES: ${step.clinical_field.toUpperCase()}`;
        document.getElementById("socratesQuestionHeading").textContent = step.question.en;
        document.getElementById("socratesQuestionVernacular").textContent = step.question[window.app.appState.currentLanguage] || step.question.hi;

        // Render Options Grid
        const grid = document.getElementById("socratesOptionsGrid");
        grid.innerHTML = "";
        step.options.forEach(opt => {
          const btn = document.createElement("button");
          btn.type = "button";
          btn.className = "socrates-option-btn";
          btn.innerHTML = `
            <span class="label-primary">${opt.label_en}</span>
            <span class="label-secondary">${opt[`label_${window.app.appState.currentLanguage}`] || opt.label_hi || ''}</span>
          `;
          btn.addEventListener("click", () => {
            document.querySelectorAll(".socrates-option-btn").forEach(b => b.classList.remove("selected"));
            btn.classList.add("selected");
            saveSocratesOption(step.clinical_field, opt.label_en);
          });
          grid.appendChild(btn);
        });

        // Speak question in Indian vernacular
        window.app.speakText(step.question[window.app.appState.currentLanguage] || step.question.hi, window.app.appState.currentLanguage);
      }
    } catch (err) {
      console.error(err);
    }
  }

  function saveSocratesOption(field, value) {
    if (field === "site") currentSessionData.socrates.site = value;
    else if (field === "onset") currentSessionData.socrates.onset = value;
    else if (field === "character") currentSessionData.socrates.character = value;
    else if (field === "radiation") currentSessionData.socrates.radiation = value;
    else if (field === "associations") {
      if (!currentSessionData.socrates.associations.includes(value)) {
        currentSessionData.socrates.associations.push(value);
      }
    }
    else if (field === "timing") currentSessionData.socrates.timing = value;
    else if (field === "exacerbating_factors") {
      currentSessionData.socrates.exacerbating_factors = [value];
    }
  }

  async function submitSocratesData() {
    try {
      const res = await fetch(`${API_BASE}/kiosk/submit-socrates`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: currentSessionData.sessionId,
          chief_complaint_id: currentSessionData.chiefComplaintId,
          chief_complaint_title: currentSessionData.chiefComplaintTitle,
          affected_body_part: currentSessionData.affectedBodyPart,
          socrates: currentSessionData.socrates
        })
      });
      const data = await res.json();
      if (data.success) {
        currentSessionData.triageResult = data.triage;
        if (data.triage && data.triage.is_red_flag) {
          window.app.showEmergencyBanner(
            document.getElementById("patientNameInput").value || "Patient",
            data.triage.clinical_rationale
          );
        }
      }
    } catch (err) {
      console.error(err);
    }
  }

  // Step 4: AYUSH Pariksha & Prakriti Scoring
  async function loadAyushQuestions() {
    try {
      const res = await fetch(`${API_BASE}/ayush/questions?language=${window.app.appState.currentLanguage}`);
      const data = await res.json();
      if (data.success) {
        renderAyushForm(data.questions);
      }
    } catch (err) {
      console.error(err);
    }
  }

  function renderAyushForm(questions) {
    const grid = document.getElementById("ayushQuestionsGrid");
    if (!grid) return;
    grid.innerHTML = "";

    questions.forEach(q => {
      const card = document.createElement("div");
      card.className = "ayush-question-card";
      card.innerHTML = `
        <div class="ayush-question-title">🌿 ${q.title} (${q.title_vernacular || ''})</div>
        <div class="ayush-radio-group">
          ${q.options.map(opt => `
            <label class="ayush-radio-label">
              <input type="radio" name="${q.id}" value="${opt.value}" ${opt.is_default ? 'checked' : ''}>
              <span>${opt.label}</span>
            </label>
          `).join('')}
        </div>
      `;
      grid.appendChild(card);
    });
  }

  async function calculateAyushPariksha() {
    const answers = {};
    document.querySelectorAll('#ayushQuestionsGrid input[type="radio"]:checked').forEach(r => {
      answers[r.name] = r.value;
    });

    const lifestyle = document.getElementById("ayushLifestyleNotes")?.value || "Sour and fermented diet, sleep after midnight.";

    try {
      const res = await fetch(`${API_BASE}/ayush/calculate-pariksha`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: currentSessionData.sessionId,
          answers,
          lifestyle_notes: lifestyle,
          language: window.app.appState.currentLanguage
        })
      });
      const data = await res.json();
      if (data.success) {
        currentSessionData.ayushResult = data.pariksha;
        renderAyushResultBadge(data.pariksha);
      }
    } catch (err) {
      console.error(err);
    }
  }

  function renderAyushResultBadge(pariksha) {
    const box = document.getElementById("ayushPrakritiResultBox");
    if (!box) return;
    box.style.display = "block";
    box.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
        <span style="font-weight:700;color:var(--ayush-primary);">Prakriti Constitution: ${pariksha.dominant_prakriti}</span>
        <span style="font-size:0.8rem;color:var(--text-muted);">Agni: ${pariksha.agni}</span>
      </div>
      <div style="display:flex;gap:8px;font-size:0.85rem;">
        <span style="background:rgba(14,165,233,0.15);padding:4px 8px;border-radius:4px;color:#38bdf8;">Vata: ${pariksha.prakriti_scores.vata}%</span>
        <span style="background:rgba(245,158,11,0.15);padding:4px 8px;border-radius:4px;color:#fbbf24;">Pitta: ${pariksha.prakriti_scores.pitta}%</span>
        <span style="background:rgba(16,185,129,0.15);padding:4px 8px;border-radius:4px;color:#34d399;">Kapha: ${pariksha.prakriti_scores.kapha}%</span>
      </div>
    `;
  }

  // Step 5: Document OCR Digitizer
  async function loadSampleDocuments() {
    try {
      const res = await fetch(`${API_BASE}/documents/sample-library`);
      const data = await res.json();
      if (data.success) {
        renderSampleDocsList(data.samples);
      }
    } catch (err) {
      console.error(err);
    }
  }

  function renderSampleDocsList(samples) {
    const list = document.getElementById("sampleDocsList");
    if (!list) return;
    list.innerHTML = "";

    samples.forEach(sample => {
      const item = document.createElement("div");
      item.className = "sample-doc-item";
      item.innerHTML = `
        <div>
          <div class="doc-title">📄 ${sample.title}</div>
          <div class="doc-meta">${sample.doctor} | ${sample.facility}</div>
        </div>
        <button type="button" class="btn btn-secondary btn-sm">1-Click OCR Load</button>
      `;
      item.addEventListener("click", () => loadSampleDocOCR(sample.id));
      list.appendChild(item);
    });
  }

  async function loadSampleDocOCR(sampleId) {
    if (!currentSessionData.sessionId) {
      await startIntakeSession();
    }
    try {
      const res = await fetch(`${API_BASE}/documents/load-sample`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: currentSessionData.sessionId,
          sample_id: sampleId
        })
      });
      const data = await res.json();
      if (data.success) {
        currentSessionData.uploadedDocuments.push(data.document);
        renderOcrResults(currentSessionData.uploadedDocuments);
        window.app.showToast(`Digitized Document: ${data.document.original_filename}`, "success");
      }
    } catch (err) {
      console.error(err);
    }
  }

  async function handleCustomDocumentUpload() {
    const rawText = document.getElementById("customDocTextInput")?.value.trim();
    if (!rawText) {
      window.app.showToast("Please enter prescription or lab text to digitize", "error");
      return;
    }
    if (!currentSessionData.sessionId) {
      await startIntakeSession();
    }

    const formData = new FormData();
    formData.append("session_id", currentSessionData.sessionId);
    formData.append("doc_type", "prescription");
    formData.append("filename", "patient_scanned_record.txt");
    formData.append("raw_text", rawText);

    try {
      const res = await fetch(`${API_BASE}/documents/upload-ocr`, {
        method: "POST",
        body: formData
      });
      const data = await res.json();
      if (data.success) {
        currentSessionData.uploadedDocuments.push(data.document);
        renderOcrResults(currentSessionData.uploadedDocuments);
        window.app.showToast("Medical document text digitized successfully!", "success");
      }
    } catch (err) {
      console.error(err);
    }
  }

  function renderOcrResults(docs) {
    const container = document.getElementById("ocrExtractedResults");
    if (!container) return;
    container.innerHTML = "";

    docs.forEach(doc => {
      const block = document.createElement("div");
      block.style.marginBottom = "14px";
      block.innerHTML = `
        <div style="font-weight:700;font-size:0.9rem;margin-bottom:6px;color:var(--primary);">
          ${doc.document_type.toUpperCase()}: ${doc.original_filename}
        </div>
      `;

      // Medications
      if (doc.extracted_medications && doc.extracted_medications.length > 0) {
        doc.extracted_medications.forEach(m => {
          block.innerHTML += `
            <div class="extracted-item-pill">
              <span>💊 <strong>${m.drug_name}</strong> (${m.strength || ''}) - ${m.dosage_frequency}</span>
              <span style="font-size:0.75rem;color:var(--text-muted);">${m.timing}</span>
            </div>
          `;
        });
      }

      // Investigations
      if (doc.extracted_investigations && doc.extracted_investigations.length > 0) {
        doc.extracted_investigations.forEach(inv => {
          const flagClass = inv.flag === "CRITICAL" ? "critical" : inv.flag === "HIGH" ? "high" : "normal";
          block.innerHTML += `
            <div class="extracted-item-pill">
              <span>🧪 ${inv.test_name}: <strong>${inv.measured_value} ${inv.unit}</strong></span>
              <span class="flag-badge ${flagClass}">${inv.flag} (${inv.reference_range})</span>
            </div>
          `;
        });
      }

      container.appendChild(block);
    });
  }

  // Step 6: Finalize Intake & OPD Token Generation
  async function finalizeIntake() {
    try {
      const res = await fetch(`${API_BASE}/kiosk/finalize-intake`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: currentSessionData.sessionId })
      });
      const data = await res.json();
      if (data.success) {
        currentSessionData.summary = data.summary;
        currentSessionData.tokenNumber = data.token_number;
        currentSessionData.triageResult = data.triage;
        renderIntakeToken(data);
        window.app.showToast("OPD Token Generated & Synced with Doctor Desk!", "success");
      }
    } catch (err) {
      console.error(err);
    }
  }

  function renderIntakeToken(data) {
    const tokenDisplay = document.getElementById("kioskTokenNumberDisplay");
    const tokenPatient = document.getElementById("kioskTokenPatientName");
    const tokenTime = document.getElementById("kioskTokenWaitTime");
    const triageBadge = document.getElementById("kioskTokenTriageBadge");
    const summaryNarrative = document.getElementById("kioskSummaryNarrative");

    if (tokenDisplay) tokenDisplay.textContent = data.token_number;
    if (tokenPatient) tokenPatient.textContent = `${document.getElementById("patientNameInput").value || 'Ramesh Kumar'} (${document.getElementById("patientAgeInput").value || '58'} Y / ${document.getElementById("patientGenderSelect").value || 'Male'})`;
    if (tokenTime) tokenTime.textContent = data.triage.is_red_flag ? "IMMEDIATE ATTENTION (Emergency Desk 01)" : "Estimated Wait: ~8 Minutes (Room 104)";

    if (triageBadge) {
      if (data.triage.is_red_flag) {
        triageBadge.className = "pulse-badge";
        triageBadge.textContent = "EMERGENCY TRIAGE RED-FLAG";
      } else {
        triageBadge.className = "dpdp-badge";
        triageBadge.textContent = "ROUTINE OPD QUEUE";
      }
    }

    if (summaryNarrative && data.summary) {
      summaryNarrative.textContent = data.summary.history_of_present_illness;
    }
  }

  // Navigation Orchestrator
  async function goToNextStep() {
    if (currentStep === 1) {
      if (!currentSessionData.sessionId) {
        const ok = await startIntakeSession();
        if (!ok) {
          window.app.showToast("Failed to initialize session. Please check inputs.", "error");
          return;
        }
      }
    } else if (currentStep === 2) {
      socratesStepIndex = 0;
      await renderSocratesInteractiveStep();
    } else if (currentStep === 3) {
      await submitSocratesData();
      if (currentSessionData.stream === "ayush") {
        await loadAyushQuestions();
      } else {
        // Skip step 4 for Allopathy stream
        navigateToStep(5);
        return;
      }
    } else if (currentStep === 4) {
      await calculateAyushPariksha();
    } else if (currentStep === 5) {
      await finalizeIntake();
    }

    if (currentStep < totalSteps) {
      navigateToStep(currentStep + 1);
    }
  }

  function goToPrevStep() {
    if (currentStep > 1) {
      if (currentStep === 5 && currentSessionData.stream !== "ayush") {
        navigateToStep(3);
      } else {
        navigateToStep(currentStep - 1);
      }
    }
  }

  function navigateToStep(stepNumber) {
    currentStep = stepNumber;

    // Toggle Content Panels
    document.querySelectorAll(".kiosk-step-content").forEach(content => {
      content.classList.toggle("active", content.id === `kioskStep${stepNumber}`);
    });

    // Toggle Stepper Sidebar
    document.querySelectorAll(".kiosk-step-item").forEach(item => {
      const step = parseInt(item.getAttribute("data-step"));
      item.classList.toggle("active", step === currentStep);
      item.classList.toggle("completed", step < currentStep);
    });

    // Update Footer Buttons
    const nextBtn = document.getElementById("kioskNextBtn");
    const prevBtn = document.getElementById("kioskPrevBtn");
    if (prevBtn) prevBtn.style.display = currentStep === 1 ? "none" : "inline-flex";
    if (nextBtn) {
      if (currentStep === totalSteps) {
        nextBtn.textContent = "Print Token / Restart";
        nextBtn.onclick = () => window.location.reload();
      } else if (currentStep === 5) {
        nextBtn.textContent = "Generate OPD Token";
      } else {
        nextBtn.textContent = "Next Step →";
      }
    }
  }

  function updateStepperUI() {
    navigateToStep(1);
  }

  function updateLanguage(langCode) {
    currentSessionData.language = langCode;
    loadChiefComplaints();
    if (currentStep === 3) {
      renderSocratesInteractiveStep();
    }
  }

  return {
    init,
    handleVoiceInput,
    updateLanguage,
    currentSessionData
  };
})();

window.kioskModule = kioskModule;
