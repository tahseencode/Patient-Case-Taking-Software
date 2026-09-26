-- =============================================================================
-- MediKiosk / AyurKiosk - Clinical Intake SQL Database Schema
-- SIH26047: AI-Powered Digital Clinical Intake Platform
-- Standards: ABDM FHIR R4, DPDP Act 2023, ICD-10, AYUSH NAMASTE
-- =============================================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------------------------
-- 1. Patients Table
-- Core demographic profile, contact details, and ABDM ABHA identifiers.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS patients (
    patient_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    age INTEGER NOT NULL,
    gender VARCHAR(32) NOT NULL,
    phone VARCHAR(32) NOT NULL,
    abha_id VARCHAR(255),
    abha_number VARCHAR(64),
    language VARCHAR(16) DEFAULT 'hi',
    stream VARCHAR(32) DEFAULT 'allopathy',
    token_number VARCHAR(32),
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_patients_phone ON patients(phone);
CREATE INDEX IF NOT EXISTS idx_patients_abha_id ON patients(abha_id);
CREATE INDEX IF NOT EXISTS idx_patients_token ON patients(token_number);

-- -----------------------------------------------------------------------------
-- 2. Consents Table (DPDP Act 2023 Compliance)
-- Cryptographic digital consent artifacts, purpose checkboxes, and SHA-256 hash.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS consents (
    consent_id VARCHAR(64) PRIMARY KEY,
    patient_id VARCHAR(64) NOT NULL,
    timestamp TEXT NOT NULL,
    voice_capture_allowed BOOLEAN DEFAULT 1,
    ocr_processing_allowed BOOLEAN DEFAULT 1,
    abha_data_sharing_allowed BOOLEAN DEFAULT 1,
    anonymized_research_allowed BOOLEAN DEFAULT 0,
    consent_version VARCHAR(32) DEFAULT 'DPDP-2023-V1.2',
    audio_consent_verified BOOLEAN DEFAULT 1,
    consent_hash VARCHAR(128) NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_consents_patient_id ON consents(patient_id);
CREATE INDEX IF NOT EXISTS idx_consents_hash ON consents(consent_hash);

-- -----------------------------------------------------------------------------
-- 3. Intake Sessions Table
-- Top-level clinical encounter session tying together patient, consent,
-- SOCRATES Q&A, AYUSH Prakriti, and triage alert.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS intake_sessions (
    session_id VARCHAR(64) PRIMARY KEY,
    patient_id VARCHAR(64) NOT NULL,
    consent_id VARCHAR(64) NOT NULL,
    chief_complaint TEXT,
    affected_body_part VARCHAR(64),
    socrates_data TEXT,              -- JSON encoded SocratesResponse
    ayush_data TEXT,                 -- JSON encoded AyushPariksha
    triage_data TEXT,                -- JSON encoded TriageAlert
    is_completed BOOLEAN DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE,
    FOREIGN KEY (consent_id) REFERENCES consents(consent_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sessions_patient_id ON intake_sessions(patient_id);
CREATE INDEX IF NOT EXISTS idx_sessions_is_completed ON intake_sessions(is_completed);
CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON intake_sessions(created_at);

-- -----------------------------------------------------------------------------
-- 4. Clinical Summaries Table
-- AI-synthesized clinical summary from SOCRATES narrative, digitized records,
-- ICD-10 suggestions, and AYUSH NAMASTE suggestions.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS clinical_summaries (
    summary_id VARCHAR(64) PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL UNIQUE,
    patient_id VARCHAR(64) NOT NULL,
    chief_complaint TEXT NOT NULL,
    duration_of_complaint VARCHAR(128),
    history_of_present_illness TEXT,
    past_medical_history TEXT,          -- JSON list of strings
    past_surgical_history TEXT,         -- JSON list of strings
    drug_allergies TEXT,                -- JSON list of strings
    current_medications TEXT,           -- JSON list of ExtractedMedication objects
    family_history TEXT,                -- JSON list of strings
    personal_and_social_history TEXT,   -- JSON object
    review_of_systems TEXT,             -- JSON object
    ayush_assessment TEXT,              -- JSON object of AyushPariksha
    investigation_summary TEXT,         -- JSON list of ExtractedLabInvestigation objects
    triage TEXT,                        -- JSON object of TriageAlert
    icd10_suggestions TEXT,             -- JSON list of suggestions
    namaste_suggestions TEXT,           -- JSON list of suggestions
    summary_generated_at TEXT NOT NULL,
    physician_reviewed BOOLEAN DEFAULT 0,
    physician_notes TEXT,
    FOREIGN KEY (session_id) REFERENCES intake_sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_summaries_session_id ON clinical_summaries(session_id);
CREATE INDEX IF NOT EXISTS idx_summaries_patient_id ON clinical_summaries(patient_id);

-- -----------------------------------------------------------------------------
-- 5. Digitized Documents Table (OCR)
-- Records uploaded prescriptions, lab reports, discharge summaries,
-- and extracted entities.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS documents (
    document_id VARCHAR(64) PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL,
    patient_id VARCHAR(64) NOT NULL,
    document_type VARCHAR(64) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    upload_timestamp TEXT NOT NULL,
    ocr_raw_text TEXT,
    extracted_diagnoses TEXT,           -- JSON list
    extracted_medications TEXT,         -- JSON list of ExtractedMedication
    extracted_investigations TEXT,      -- JSON list of ExtractedLabInvestigation
    historical_date VARCHAR(64),
    doctor_or_facility VARCHAR(255),
    FOREIGN KEY (session_id) REFERENCES intake_sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_documents_session_id ON documents(session_id);
CREATE INDEX IF NOT EXISTS idx_documents_patient_id ON documents(patient_id);

-- -----------------------------------------------------------------------------
-- 6. Doctor Consultations Table
-- Completed doctor prescriptions, diagnoses, ABDM FHIR bundle IDs, and clinical notes.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS consultations (
    consultation_id VARCHAR(64) PRIMARY KEY,
    session_id VARCHAR(64) NOT NULL UNIQUE,
    patient_id VARCHAR(64) NOT NULL,
    doctor_name VARCHAR(255) NOT NULL,
    doctor_department VARCHAR(255) NOT NULL,
    diagnosis TEXT NOT NULL,
    icd10_code VARCHAR(64),
    ayush_namaste_code VARCHAR(64),
    clinical_notes TEXT,
    prescriptions TEXT,                 -- JSON list of DoctorPrescriptionItem
    ordered_investigations TEXT,        -- JSON list of strings
    follow_up_date VARCHAR(128),
    consultation_timestamp TEXT NOT NULL,
    fhir_bundle_id VARCHAR(128),
    FOREIGN KEY (session_id) REFERENCES intake_sessions(session_id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(patient_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_consultations_session_id ON consultations(session_id);
CREATE INDEX IF NOT EXISTS idx_consultations_patient_id ON consultations(patient_id);

-- -----------------------------------------------------------------------------
-- 7. OPD Waiting Queue Table
-- Live OPD waiting line for allopathy and AYUSH streams.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS opd_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token VARCHAR(32) NOT NULL,
    session_id VARCHAR(64) NOT NULL UNIQUE,
    patient_id VARCHAR(64) NOT NULL,
    patient_name VARCHAR(255) NOT NULL,
    age INTEGER NOT NULL,
    gender VARCHAR(32) NOT NULL,
    chief_complaint TEXT,
    stream VARCHAR(32) DEFAULT 'allopathy',
    triage_level VARCHAR(32) DEFAULT 'routine',
    is_red_flag BOOLEAN DEFAULT 0,
    waiting_minutes INTEGER DEFAULT 0,
    summary_id VARCHAR(64),
    has_scanned_docs BOOLEAN DEFAULT 0,
    status VARCHAR(32) DEFAULT 'waiting', -- waiting, in_consultation, completed
    created_at TEXT NOT NULL,
    FOREIGN KEY (session_id) REFERENCES intake_sessions(session_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_queue_status ON opd_queue(status);
CREATE INDEX IF NOT EXISTS idx_queue_session_id ON opd_queue(session_id);
CREATE INDEX IF NOT EXISTS idx_queue_token ON opd_queue(token);

-- -----------------------------------------------------------------------------
-- 8. Emergency Triage Alerts Table
-- Red-flag emergency notifications for immediate clinical intervention.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS triage_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token VARCHAR(32) NOT NULL,
    patient_name VARCHAR(255) NOT NULL,
    rationale TEXT NOT NULL,
    action TEXT NOT NULL,
    is_resolved BOOLEAN DEFAULT 0,
    timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_triage_resolved ON triage_alerts(is_resolved);
CREATE INDEX IF NOT EXISTS idx_triage_token ON triage_alerts(token);

-- -----------------------------------------------------------------------------
-- 9. ABDM / DPDP Compliance Audit Logs Table
-- Immutable audit log for healthcare data access and consent verification.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type VARCHAR(64) NOT NULL,
    patient_id VARCHAR(64),
    session_id VARCHAR(64),
    facility_id VARCHAR(64),
    details TEXT,
    timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_audit_event ON audit_logs(event_type);
CREATE INDEX IF NOT EXISTS idx_audit_patient ON audit_logs(patient_id);
