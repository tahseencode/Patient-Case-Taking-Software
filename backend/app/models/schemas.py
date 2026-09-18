from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class LanguageEnum(str, Enum):
    EN = "en"
    HI = "hi"
    MR = "mr"
    TA = "ta"
    TE = "te"
    BN = "bn"
    GU = "gu"
    KN = "kn"

class StreamEnum(str, Enum):
    ALLOPATHY = "allopathy"
    AYUSH = "ayush"

class TriageLevel(str, Enum):
    RED = "emergency"      # Immediate intervention required (e.g. STEMI, Stroke, Acute Dyspnea)
    YELLOW = "priority"    # Urgent attention needed (e.g. High fever, Severe pain, High BP)
    GREEN = "routine"      # Standard OPD routine queue

class DPDP2023Consent(BaseModel):
    consent_id: str
    patient_id: str
    timestamp: str
    voice_capture_allowed: bool = True
    ocr_processing_allowed: bool = True
    abha_data_sharing_allowed: bool = True
    anonymized_research_allowed: bool = False
    consent_version: str = "DPDP-2023-V1.2"
    audio_consent_verified: bool = True
    consent_hash: str = ""

class PatientDemographics(BaseModel):
    patient_id: str
    name: str
    age: int
    gender: str
    phone: str
    abha_id: Optional[str] = None
    abha_number: Optional[str] = None
    language: LanguageEnum = LanguageEnum.HI
    stream: StreamEnum = StreamEnum.ALLOPATHY
    token_number: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class SocratesResponse(BaseModel):
    site: Optional[str] = None                    # Where is the symptom/pain?
    onset: Optional[str] = None                   # When and how did it start? (sudden/gradual)
    character: Optional[str] = None               # What does it feel like? (sharp/dull/throbbing/burning/tight)
    radiation: Optional[str] = None               # Does it spread anywhere? (e.g. left arm, back, jaw)
    associations: Optional[List[str]] = []        # Sweating, nausea, vomiting, dizziness, breathlessness
    timing: Optional[str] = None                  # Constant, intermittent, specific times of day
    exacerbating_factors: Optional[List[str]] = []# Walking, food, deep breath, lying down
    relieving_factors: Optional[List[str]] = []   # Rest, medications, sitting upright
    severity_score: Optional[int] = 5             # 1 to 10 scale

class DialogueTurn(BaseModel):
    step_id: str
    question_text: Dict[str, str]                 # Multilingual questions { "en": "...", "hi": "..." }
    audio_prompt_url: Optional[str] = None
    question_type: str                            # "socrates", "body_map", "multi_choice", "scale", "open_voice"
    options: Optional[List[Dict[str, str]]] = []  # [{ "value": "sharp", "label_en": "Sharp", "label_hi": "तेज़" }]
    body_region_filter: Optional[str] = None
    clinical_field: str

class AyushPariksha(BaseModel):
    prakriti_scores: Dict[str, float] = { "vata": 0.0, "pitta": 0.0, "kapha": 0.0 }
    dominant_prakriti: str = "Sama (Balanced)"
    agni: str = "Sama Agni (Normal)"              # Manda (Low), Tikshna (High), Vishama (Irregular), Sama (Balanced)
    koshtha: str = "Madhyama Koshtha"             # Krura (Hard/Constipated), Mridu (Soft/Loose), Madhyama (Regular)
    sara: str = "Madhyama Sara"                   # Dhatu excellence
    samhanana: str = "Madhyama"                   # Body compactness
    pramana: str = "Madhyama"                     # Anthropometry
    satmya: str = "Sarva Rasa Satmya"             # Adaptability
    sattva: str = "Madhyama Sattva"               # Mental strength
    ahara_shakti: str = "Madhyama"                # Digestive capacity
    vyayama_shakti: str = "Madhyama"              # Physical endurance
    vaya: str = "Madhyama (Adult)"                # Age group
    ahara_vihara_notes: Optional[str] = None      # Diet, sleep, day routine
    nidana_causative_factors: Optional[List[str]] = []

class ExtractedMedication(BaseModel):
    drug_name: str
    strength: Optional[str] = None
    dosage_form: Optional[str] = "Tablet"          # Tablet, Capsule, Syrup, Injection
    dosage_frequency: Optional[str] = "1-0-1"      # Morning-Afternoon-Night
    timing: Optional[str] = "After Food"           # Before/After food
    duration: Optional[str] = "5 days"

class ExtractedLabInvestigation(BaseModel):
    test_name: str
    measured_value: str
    reference_range: str
    unit: str
    is_abnormal: bool = False
    flag: Optional[str] = "NORMAL"                 # "HIGH", "LOW", "CRITICAL", "NORMAL"
    test_date: Optional[str] = None

class DocumentDigitization(BaseModel):
    document_id: str
    patient_id: str
    document_type: str                            # "prescription", "lab_report", "discharge_summary", "radiology"
    original_filename: str
    upload_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    ocr_raw_text: str
    extracted_diagnoses: List[str] = []
    extracted_medications: List[ExtractedMedication] = []
    extracted_investigations: List[ExtractedLabInvestigation] = []
    historical_date: Optional[str] = None
    doctor_or_facility: Optional[str] = None

class TriageAlert(BaseModel):
    is_red_flag: bool = False
    triage_level: TriageLevel = TriageLevel.GREEN
    severity_score: int = 1                       # 1-10
    detected_symptoms: List[str] = []
    clinical_rationale: str = ""
    recommended_action: str = "Proceed to routine OPD queue"
    alert_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class StructuredClinicalSummary(BaseModel):
    summary_id: str
    patient_id: str
    chief_complaint: str
    duration_of_complaint: str
    history_of_present_illness: str               # Detailed narrative synthesized from SOCRATES
    past_medical_history: List[str] = []
    past_surgical_history: List[str] = []
    drug_allergies: List[str] = []
    current_medications: List[ExtractedMedication] = []
    family_history: List[str] = []
    personal_and_social_history: Dict[str, Any] = {}
    review_of_systems: Dict[str, List[str]] = {}
    ayush_assessment: Optional[AyushPariksha] = None
    investigation_summary: List[ExtractedLabInvestigation] = []
    triage: TriageAlert
    icd10_suggestions: List[Dict[str, str]] = []
    namaste_suggestions: List[Dict[str, str]] = []
    summary_generated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    physician_reviewed: bool = False
    physician_notes: Optional[str] = None

class DoctorPrescriptionItem(BaseModel):
    medicine_name: str
    dosage: str
    frequency: str
    duration: str
    instructions: str

class DoctorConsultationRecord(BaseModel):
    consultation_id: str
    patient_id: str
    doctor_name: str
    doctor_department: str
    diagnosis: str
    icd10_code: Optional[str] = None
    ayush_namaste_code: Optional[str] = None
    clinical_notes: str
    prescriptions: List[DoctorPrescriptionItem] = []
    ordered_investigations: List[str] = []
    follow_up_date: Optional[str] = None
    consultation_timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    fhir_bundle_id: Optional[str] = None

class IntakeSession(BaseModel):
    session_id: str
    patient: PatientDemographics
    consent: DPDP2023Consent
    chief_complaint: Optional[str] = None
    affected_body_part: Optional[str] = None
    socrates: SocratesResponse = Field(default_factory=SocratesResponse)
    ayush: Optional[AyushPariksha] = None
    documents: List[DocumentDigitization] = []
    triage: TriageAlert = Field(default_factory=TriageAlert)
    summary: Optional[StructuredClinicalSummary] = None
    is_completed: bool = False
