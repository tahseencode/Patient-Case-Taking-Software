/**
 * MediKiosk AI & AyurKiosk - Global Application Core & State Engine
 * SIH26047: AI-Powered Digital Clinical Intake & AYUSH OPD Platform
 */

const API_BASE = "/api/v1";

// Global State
const appState = {
  currentRole: "kiosk",         // "kiosk" | "doctor" | "analytics" | "fhir"
  currentLanguage: "hi",        // "en" | "hi" | "mr" | "ta" | "te" | "bn" | "gu" | "kn"
  theme: "light",
  currentSession: null,
  activeQueueItem: null,
  websocket: null,
  isRecording: false,
  recognition: null
};

// Multilingual Localization Dictionary
const I18N = {
  en: {
    appTitle: "Swasthya Sathi Care Desk",
    appSub: "SIH26047: Digital Clinical Intake & AYUSH OPD Desk",
    tabKiosk: "Patient Intake Kiosk",
    tabDoctor: "Doctor OPD Desk",
    tabAnalytics: "OPD Analytics",
    tabFhir: "ABDM FHIR Hub",
    redFlagAlert: "EMERGENCY TRIAGE RED-FLAG INTERCEPTED",
    startIntake: "Start Intake",
    nextStep: "Next Step",
    prevStep: "Previous",
    finishIntake: "Generate OPD Token",
    abhaVerified: "ABDM ABHA Verified",
    voicePrompt: "Tap Mic to Speak in Your Language",
    speaking: "Listening... Speak now",
    severityLabel: "Pain / Discomfort Intensity (1 to 10)",
    sampleDocsTitle: "Load Sample Patient Records",
    saveAndPrescribe: "Save & Generate ABDM FHIR Record"
  },
  hi: {
    appTitle: "स्वास्थ्य साथी - डिजिटल मरीज पर्चा प्रणाली",
    appSub: "डिजिटल क्लिनिकल इनटेक एवं आयुष ओपीडी मंच",
    tabKiosk: "मरीज इनटेक कियोस्क",
    tabDoctor: "चिकित्सक ओपीडी डेस्क",
    tabAnalytics: "ओपीडी विश्लेषण",
    tabFhir: "आयुष्मान भारत (ABDM) हब",
    redFlagAlert: "आपातकालीन चेतावनी: गंभीर लक्षण पाए गए!",
    startIntake: "प्रक्रिया शुरू करें",
    nextStep: "अगला कदम",
    prevStep: "पिछला",
    finishIntake: "ओपीडी टोकन प्राप्त करें",
    abhaVerified: "आभा (ABHA) आईडी सत्यापित",
    voicePrompt: "बोलकर बताने के लिए माइक दबाएं",
    speaking: "सुन रहे हैं... कृपया बोलें",
    severityLabel: "दर्द / परेशानी की तीव्रता (1 से 10)",
    sampleDocsTitle: "नमूना पुराने पर्चे व रिपोर्ट लोड करें",
    saveAndPrescribe: "पर्चा पूर्ण करें व ABDM रिकॉर्ड बनाएं"
  },
  mr: {
    appTitle: "मेडीकियोस्क एआय",
    appSub: "डिजिटल क्लिनिकल इनटेक व आयुष ओपीडी",
    tabKiosk: "रुग्ण तपासणी कियोस्क",
    tabDoctor: "डॉक्टर ओपीडी कक्ष",
    tabAnalytics: "ओपीडी आकडेवारी",
    tabFhir: "ABDM FHIR हब",
    redFlagAlert: "तातडीची सूचना: गंभीर लक्षणे आढळली!",
    startIntake: "सुरुवात करा",
    nextStep: "पुढील पायरी",
    prevStep: "मागे",
    finishIntake: "ओपीडी टोकन मिळवा",
    abhaVerified: "आभा आयडी पडताळणी पूर्ण",
    voicePrompt: "बोलण्यासाठी माइक दाबा",
    speaking: "ऐकत आहोत... बोला",
    severityLabel: "वेदनेची तीव्रता (१ ते १०)",
    sampleDocsTitle: "नमुने दाखल करा",
    saveAndPrescribe: "सल्ला जतन करा व ABDM नोंद करा"
  },
  ta: {
    appTitle: "மெடிகியோஸ்க் AI",
    appSub: "டிஜிட்டல் மருத்துவ உட்கொள்ளல் தளம்",
    tabKiosk: "நோயாளி கியோஸ்க்",
    tabDoctor: "மருத்துவர் ஓபிடி தளம்",
    tabAnalytics: "ஓபிடி புள்ளிவிவரங்கள்",
    tabFhir: "ABDM FHIR மையம்",
    redFlagAlert: "அவசர சிகிச்சை எச்சரிக்கை!",
    startIntake: "தொடங்கவும்",
    nextStep: "அடுத்த படி",
    prevStep: "முந்தைய",
    finishIntake: "டோக்கன் பெறுக",
    abhaVerified: "ABHA சரிபார்க்கப்பட்டது",
    voicePrompt: "பேச மைக்கை அழுத்தவும்",
    speaking: "கேட்கிறது... பேசுங்கள்",
    severityLabel: "வலியின் தீவிரம் (1 முதல் 10)",
    sampleDocsTitle: "மாதிரி ஆவணங்களை ஏற்றவும்",
    saveAndPrescribe: "பரிந்துரைத்து சேமிக்கவும்"
  },
  te: {
    appTitle: "మెడికియోస్క్ AI",
    appSub: "డిజిటల్ క్లినికల్ ఇంటెక్ ప్లాట్‌ఫారమ్",
    tabKiosk: "రోగి కియోస్క్",
    tabDoctor: "డాక్టర్ ఓపీడీ డెస్క్",
    tabAnalytics: "ఓపీడీ విశ్లేషణ",
    tabFhir: "ABDM FHIR హబ్",
    redFlagAlert: "అత్యవసర ట్రయేజ్ హెచ్చరిక!",
    startIntake: "ప్రారంభించండి",
    nextStep: "తదుపరి దశ",
    prevStep: "వెనుకకు",
    finishIntake: "ఓపీడీ టోకెన్ పొందండి",
    abhaVerified: "ABHA ధృవీకరించబడింది",
    voicePrompt: "మాట్లాడటానికి మైక్ నొక్కండి",
    speaking: "వింటున్నాము... మాట్లాడండి",
    severityLabel: "నొప్పి తీవ్రత (1 నుండి 10)",
    sampleDocsTitle: "నమూనా పత్రాలను లోడ్ చేయండి",
    saveAndPrescribe: "ప్రిస్క్రిప్షన్ పూర్తి చేయండి"
  },
  bn: {
    appTitle: "মেডিকিয়স্ক এআই",
    appSub: "ডিজিটাল ক্লিনিক্যাল ইনটেক ও আয়ুষ ওপিডি",
    tabKiosk: "রোগী ইনটেক কিয়স্ক",
    tabDoctor: "ডাক্তার ওপিডি ডেস্ক",
    tabAnalytics: "ওপিডি বিশ্লেষণ",
    tabFhir: "ABDM FHIR হাব",
    redFlagAlert: "জরুরী সতর্কতা: আশঙ্কাজনক লক্ষণ!",
    startIntake: "শুরু করুন",
    nextStep: "পরবর্তী ধাপ",
    prevStep: "পূর্ববর্তী",
    finishIntake: "ওপিডি টোকেন নিন",
    abhaVerified: "ABHA আইডি যাচাইকৃত",
    voicePrompt: "কথা বলতে মাইক চাপুন",
    speaking: "শুনছি... বলুন",
    severityLabel: "ব্যথার তীব্রতা (১ থেকে ১০)",
    sampleDocsTitle: "নমুনা রিপোর্ট লোড করুন",
    saveAndPrescribe: "প্রেসক্রিপশন সম্পন্ন করুন"
  },
  gu: {
    appTitle: "મેડીકિયોસ્ક AI",
    appSub: "ડિજિટલ ક્લિનિકલ ઇન્ટેક પ્લેટફોર્મ",
    tabKiosk: "દર્દી ઇન્ટેક કિઓસ્ક",
    tabDoctor: "ડોક્ટર ઓપીડી ડેસ્ક",
    tabAnalytics: "ઓપીડી એનાલિટિક્સ",
    tabFhir: "ABDM FHIR હબ",
    redFlagAlert: "ઇમરજન્સી ચેતવણી: ગંભીર લક્ષણ!",
    startIntake: "શરૂ કરો",
    nextStep: "આગળનું પગલું",
    prevStep: "પાછળ",
    finishIntake: "ઓપીડી ટોકન મેળવો",
    abhaVerified: "ABHA ચકાસાયેલ છે",
    voicePrompt: "બોલવા માટે માઇક દબાવો",
    speaking: "સાંભળી રહ્યા છીએ... બોલો",
    severityLabel: "દુખાવાની તીવ્રતા (૧ થી ૧૦)",
    sampleDocsTitle: "નમૂના રિપોર્ટ લોડ કરો",
    saveAndPrescribe: "પ્રિસ્ક્રિપ્શન પૂર્ણ કરો"
  },
  kn: {
    appTitle: "ಮೆಡಿಕಿಯೋಸ್ಕ್ AI",
    appSub: "ಡಿಜಿಟಲ್ ಕ್ಲಿನಿಕಲ್ ಇಂಟೆಕ್ ಪ್ಲಾಟ್‌ಫಾರ್ಮ್",
    tabKiosk: "ರೋಗಿ ಇಂಟೆಕ್ ಕಿಯೋಸ್ಕ್",
    tabDoctor: "ವೈದ್ಯರ ಒಪಿಡಿ ಡೆಸ್ಕ್",
    tabAnalytics: "ಒಪಿಡಿ ವಿಶ್ಲೇಷಣೆ",
    tabFhir: "ABDM FHIR ಹಬ್",
    redFlagAlert: "ತುರ್ತು ಎಚ್ಚರಿಕೆ!",
    startIntake: "ಪ್ರಾರಂಭಿಸಿ",
    nextStep: "ಮುಂದಿನ ಹಂತ",
    prevStep: "ಹಿಂದಿನ",
    finishIntake: "ಒಪಿಡಿ ಟೋಕನ್ ಪಡೆಯಿರಿ",
    abhaVerified: "ABHA ಪರಿಶೀಲಿಸಲಾಗಿದೆ",
    voicePrompt: "ಮಾತನಾಡಲು ಮೈಕ್ ಒತ್ತಿ",
    speaking: "ಕೇಳುತ್ತಿದ್ದೇವೆ... ಮಾತನಾಡಿ",
    severityLabel: "ನೋವಿನ ತೀವ್ರತೆ (೧ ರಿಂದ ೧೦)",
    sampleDocsTitle: "ಮಾದರಿ ದಾಖಲೆಗಳನ್ನು ಲೋಡ್ ಮಾಡಿ",
    saveAndPrescribe: "ಪ್ರಿಸ್ಕ್ರಿಪ್ಷನ್ ಪೂರ್ಣಗೊಳಿಸಿ"
  }
};

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  initNavigation();
  initLanguage();
  initSpeechEngine();
  initWebSocket();

  // Initialize Child Modules
  if (window.kioskModule) window.kioskModule.init();
  if (window.doctorModule) window.doctorModule.init();
  if (window.analyticsModule) window.analyticsModule.init();
  if (window.fhirModule) window.fhirModule.init();

  showToast("MediKiosk AI Ready. ABDM Facility ID: IN-AIIMS-DELHI-0012", "info");
});

// Theme Management
function initTheme() {
  const themeToggleBtn = document.getElementById("themeToggleBtn");
  // Always force light whitish theme by default
  setTheme("light");

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener("click", () => {
      const newTheme = appState.theme === "dark" ? "light" : "dark";
      setTheme(newTheme);
    });
  }
}

function setTheme(theme) {
  appState.theme = theme;
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("medikiosk_theme", theme);
  const icon = document.querySelector("#themeToggleBtn i, #themeToggleBtn span");
  if (icon) {
    icon.textContent = theme === "dark" ? "☀️" : "🌙";
  }
}

// Navigation & Tab Switching
function initNavigation() {
  const tabs = document.querySelectorAll(".nav-tab-btn");
  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      const targetView = tab.getAttribute("data-target");
      switchRole(targetView);
    });
  });
}

function switchRole(roleName) {
  appState.currentRole = roleName;

  // Update Tab Buttons
  document.querySelectorAll(".nav-tab-btn").forEach(t => {
    t.classList.toggle("active", t.getAttribute("data-target") === roleName);
  });

  // Update Sections
  document.querySelectorAll(".view-section").forEach(sec => {
    sec.classList.toggle("active", sec.id === `${roleName}Section`);
  });

  // Trigger role specific refreshes
  if (roleName === "doctor" && window.doctorModule) {
    window.doctorModule.refreshQueue();
  } else if (roleName === "analytics" && window.analyticsModule) {
    window.analyticsModule.loadMetrics();
  } else if (roleName === "fhir" && window.fhirModule) {
    window.fhirModule.refreshCurrentBundle();
  }
}

// Language Engine
function initLanguage() {
  const langSelect = document.getElementById("globalLangSelect");
  if (langSelect) {
    langSelect.value = appState.currentLanguage;
    langSelect.addEventListener("change", (e) => {
      setLanguage(e.target.value);
    });
  }
}

function setLanguage(langCode) {
  appState.currentLanguage = langCode;
  const dict = I18N[langCode] || I18N.en;

  // Update localized text nodes with data-i18n attribute
  document.querySelectorAll("[data-i18n]").forEach(el => {
    const key = el.getAttribute("data-i18n");
    if (dict[key]) {
      el.textContent = dict[key];
    }
  });

  // Re-fetch localized content in kiosk module
  if (window.kioskModule) {
    window.kioskModule.updateLanguage(langCode);
  }
}

// Speech Recognition & TTS Synthesis
function initSpeechEngine() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition) {
    appState.recognition = new SpeechRecognition();
    appState.recognition.continuous = false;
    appState.recognition.interimResults = false;

    appState.recognition.onstart = () => {
      appState.isRecording = true;
      updateVoiceUI(true, "Listening... Speak your symptoms clearly.");
    };

    appState.recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      updateVoiceUI(false, `Recorded: "${transcript}"`);
      if (window.kioskModule) {
        window.kioskModule.handleVoiceInput(transcript);
      }
    };

    appState.recognition.onerror = (e) => {
      console.warn("Speech recognition error:", e);
      updateVoiceUI(false, "Voice processed or microphone standby.");
    };

    appState.recognition.onend = () => {
      appState.isRecording = false;
      updateVoiceUI(false, "Tap microphone to speak again.");
    };
  }
}

function toggleVoiceRecording(chiefComplaintId = null) {
  if (!appState.recognition) {
    // Offline simulated speech trigger for testing or non-supported browsers
    simulateVoiceInput(chiefComplaintId);
    return;
  }

  if (appState.isRecording) {
    appState.recognition.stop();
  } else {
    // Set speech language mapping
    const langMap = {
      en: "en-IN",
      hi: "hi-IN",
      mr: "mr-IN",
      ta: "ta-IN",
      te: "te-IN",
      bn: "bn-IN",
      gu: "gu-IN",
      kn: "kn-IN"
    };
    appState.recognition.lang = langMap[appState.currentLanguage] || "hi-IN";
    try {
      appState.recognition.start();
    } catch (err) {
      simulateVoiceInput(chiefComplaintId);
    }
  }
}

function simulateVoiceInput(chiefComplaintId) {
  const simulatedHindiPhrases = [
    "मुझे कल रात से छाती में बहुत तेज़ जकड़न और भारीपन लग रहा है जो बाएं हाथ तक जा रहा है और बहुत पसीना आ रहा है।",
    "मुझे पिछले तीन दिनों से घुटनों में बहुत तेज दर्द और अकड़न है, चलने में कट-कट की आवाज आती है।",
    "मुझे 2 दिनों से तेज बुखार और कंपकंपी के साथ खांसी हो रही है।"
  ];
  const phrase = simulatedHindiPhrases[Math.floor(Math.random() * simulatedHindiPhrases.length)];
  updateVoiceUI(true, "Simulating speech recognition in Hindi...");
  setTimeout(() => {
    updateVoiceUI(false, `Recorded: "${phrase}"`);
    if (window.kioskModule) {
      window.kioskModule.handleVoiceInput(phrase);
    }
  }, 900);
}

function speakText(text, lang = "hi") {
  if (!window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  const langMap = { en: "en-IN", hi: "hi-IN", mr: "mr-IN", ta: "ta-IN", te: "te-IN", bn: "bn-IN", gu: "gu-IN", kn: "kn-IN" };
  utterance.lang = langMap[lang] || "hi-IN";
  utterance.rate = 0.95;
  window.speechSynthesis.speak(utterance);
}

function updateVoiceUI(isRecording, message) {
  const micBtn = document.getElementById("voiceMicBtn");
  const statusLabel = document.getElementById("voiceStatusLabel");
  const transcriptPreview = document.getElementById("voiceTranscriptPreview");

  if (micBtn) {
    micBtn.classList.toggle("recording", isRecording);
  }
  if (statusLabel) {
    statusLabel.textContent = isRecording ? "Recording in progress..." : "Voice Input Ready";
  }
  if (transcriptPreview) {
    transcriptPreview.textContent = message;
  }
}

// WebSocket Live OPD Sync
function initWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/live-feed`;

  try {
    appState.websocket = new WebSocket(wsUrl);
    appState.websocket.onopen = () => {
      console.log("WebSocket Live OPD Feed Connected.");
    };
    appState.websocket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "TRIAGE_EMERGENCY") {
        showEmergencyBanner(data.patient_name, data.rationale);
      } else if (data.type === "QUEUE_UPDATE") {
        if (window.doctorModule) window.doctorModule.refreshQueue();
        if (window.analyticsModule) window.analyticsModule.loadMetrics();
      }
    };
    appState.websocket.onerror = () => {
      console.warn("WebSocket fallback mode active.");
    };
  } catch (e) {
    console.warn("WebSocket not supported in current environment.");
  }
}

function showEmergencyBanner(patientName, rationale) {
  const ticker = document.getElementById("emergencyTicker");
  const tickerText = document.getElementById("emergencyTickerText");
  if (ticker && tickerText) {
    tickerText.textContent = `RED-FLAG TRIAGE ALERT: Patient ${patientName} - ${rationale}`;
    ticker.classList.add("visible");
  }
}

// Toast Notifications
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer") || createToastContainer();
  const toast = document.createElement("div");
  toast.className = `toast-item toast-${type}`;
  toast.innerHTML = `
    <div style="display:flex;align-items:center;gap:8px;">
      <span>${type === "error" ? "⚠️" : type === "success" ? "✅" : "ℹ️"}</span>
      <span>${message}</span>
    </div>
  `;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

function createToastContainer() {
  const c = document.createElement("div");
  c.id = "toastContainer";
  c.style.cssText = "position:fixed;bottom:20px;right:20px;z-index:9999;display:flex;flex-direction:column;gap:8px;";
  document.body.appendChild(c);
  return c;
}

window.app = {
  appState,
  API_BASE,
  switchRole,
  setLanguage,
  toggleVoiceRecording,
  speakText,
  showToast,
  showEmergencyBanner
};
