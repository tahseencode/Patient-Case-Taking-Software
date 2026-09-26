-- =============================================================================
-- MediKiosk / AyurKiosk - Seed Data SQL Script
-- SIH26047: AI-Powered Digital Clinical Intake Platform
-- =============================================================================

PRAGMA foreign_keys = ON;

-- 1. Demo Patient 1: Ramesh Kumar (Allopathy / Cardiology)
INSERT INTO patients (
    patient_id, name, age, gender, phone,
    abha_id, abha_number, language, stream,
    token_number, created_at
) VALUES (
    'P-101', 'Ramesh Kumar', 58, 'Male', '9876543210',
    'ramesh.kumar58@abdm', '91-4829-1029-4412', 'hi', 'allopathy',
    'OPD-A04', datetime('now')
) ON CONFLICT(patient_id) DO NOTHING;

-- Consent for P-101
INSERT INTO consents (
    consent_id, patient_id, timestamp,
    voice_capture_allowed, ocr_processing_allowed,
    abha_data_sharing_allowed, anonymized_research_allowed,
    consent_version, audio_consent_verified, consent_hash
) VALUES (
    'DPDP-SEED-01', 'P-101', datetime('now'),
    1, 1, 1, 0,
    'DPDP-2023-V1.2', 1, '9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08'
) ON CONFLICT(consent_id) DO NOTHING;

-- Session for P-101
INSERT INTO intake_sessions (
    session_id, patient_id, consent_id,
    chief_complaint, affected_body_part,
    socrates_data, ayush_data, triage_data,
    is_completed, created_at, updated_at
) VALUES (
    'SESS-101', 'P-101', 'DPDP-SEED-01',
    'Chest Heaviness & Diabetes Checkup', 'chest',
    '{"site": "Center of chest / epigastric region", "onset": "2 to 3 days ago", "character": "Dull aching pressure", "radiation": "No radiation", "associations": ["Mild fatigue"], "timing": "Intermittent", "exacerbating_factors": ["Exertion"], "relieving_factors": ["Rest"], "severity_score": 4}',
    NULL,
    '{"is_red_flag": false, "triage_level": "routine", "severity_score": 4, "detected_symptoms": ["Dull chest heaviness on exertion"], "clinical_rationale": "Stable vitals, chronic diabetic follow-up.", "recommended_action": "Normal OPD queue allocation.", "alert_timestamp": "' || datetime('now') || '"}',
    1, datetime('now'), datetime('now')
) ON CONFLICT(session_id) DO NOTHING;

-- OPD Queue for P-101
INSERT INTO opd_queue (
    token, session_id, patient_id, patient_name,
    age, gender, chief_complaint, stream,
    triage_level, is_red_flag, waiting_minutes,
    summary_id, has_scanned_docs, status, created_at
) VALUES (
    'OPD-A04', 'SESS-101', 'P-101', 'Ramesh Kumar',
    58, 'Male', 'Chest Heaviness & Diabetes Checkup', 'allopathy',
    'routine', 0, 8,
    'SUM-SEED-01', 1, 'waiting', datetime('now')
) ON CONFLICT(session_id) DO NOTHING;

-- 2. Demo Patient 2: Shanti Devi (AYUSH / Sandhigata Vata)
INSERT INTO patients (
    patient_id, name, age, gender, phone,
    abha_id, abha_number, language, stream,
    token_number, created_at
) VALUES (
    'P-102', 'Shanti Devi', 52, 'Female', '9812345678',
    'shanti.devi52@abdm', '91-5512-8821-9901', 'hi', 'ayush',
    'AYU-B12', datetime('now')
) ON CONFLICT(patient_id) DO NOTHING;

-- Consent for P-102
INSERT INTO consents (
    consent_id, patient_id, timestamp,
    voice_capture_allowed, ocr_processing_allowed,
    abha_data_sharing_allowed, anonymized_research_allowed,
    consent_version, audio_consent_verified, consent_hash
) VALUES (
    'DPDP-SEED-02', 'P-102', datetime('now'),
    1, 1, 1, 0,
    'DPDP-2023-V1.2', 1, '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8'
) ON CONFLICT(consent_id) DO NOTHING;

-- Session for P-102
INSERT INTO intake_sessions (
    session_id, patient_id, consent_id,
    chief_complaint, affected_body_part,
    socrates_data, ayush_data, triage_data,
    is_completed, created_at, updated_at
) VALUES (
    'SESS-102', 'P-102', 'DPDP-SEED-02',
    'Bilateral Knee Joint Pain & Acidity', 'joints',
    NULL,
    '{"prakriti_scores": {"vata": 54.0, "pitta": 30.0, "kapha": 16.0}, "dominant_prakriti": "Vata Dominant (Pitta Anubandha)", "agni": "Manda Agni (Sluggish/Slow Digestion)", "koshtha": "Krura Koshtha (Hard/Costive - Vata)", "sara": "Madhyama Sara", "samhanana": "Madhyama", "pramana": "Madhyama", "satmya": "Madhyama Satmya", "sattva": "Madhyama Sattva", "ahara_shakti": "Moderate", "vyayama_shakti": "Avara (Reduced due to joint pain)", "vaya": "Madhyama Vaya", "ahara_vihara_notes": "High intake of sour & fermented food; late night sleeping; cold exposure exacerbates pain.", "nidana_causative_factors": ["Vidahi Ahara Sevana (Excess sour/pungent food causing Amlapitta)", "Vata Prakopa Nidana (Cold climate and dry food aggravating Sandhi Vata)"]}',
    '{"is_red_flag": false, "triage_level": "routine", "severity_score": 5, "detected_symptoms": ["Bilateral Knee Pain (Sandhigata Vata)", "Hyperacidity (Amlapitta)"], "clinical_rationale": "Chronic degenerative joint disease with Pitta-Vata imbalance.", "recommended_action": "AYUSH Kayachikitsa & Panchakarma OPD.", "alert_timestamp": "' || datetime('now') || '"}',
    1, datetime('now'), datetime('now')
) ON CONFLICT(session_id) DO NOTHING;

-- OPD Queue for P-102
INSERT INTO opd_queue (
    token, session_id, patient_id, patient_name,
    age, gender, chief_complaint, stream,
    triage_level, is_red_flag, waiting_minutes,
    summary_id, has_scanned_docs, status, created_at
) VALUES (
    'AYU-B12', 'SESS-102', 'P-102', 'Shanti Devi',
    52, 'Female', 'Bilateral Knee Joint Pain & Acidity', 'ayush',
    'routine', 0, 15,
    'SUM-SEED-02', 1, 'waiting', datetime('now')
) ON CONFLICT(session_id) DO NOTHING;
