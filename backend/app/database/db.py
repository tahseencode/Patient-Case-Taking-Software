import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime
from backend.app.models.schemas import (
    IntakeSession, PatientDemographics, DPDP2023Consent,
    SocratesResponse, AyushPariksha, TriageAlert, TriageLevel,
    StructuredClinicalSummary, DoctorConsultationRecord,
    ExtractedMedication, ExtractedLabInvestigation, DocumentDigitization
)
from backend.app.core.ocr_engine import ocr_engine
from backend.app.sample_data.sample_documents import SAMPLE_DOCUMENTS

class InMemoryDB:
    def __init__(self):
        self.sessions: Dict[str, IntakeSession] = {}
        self.opd_queue: List[Dict[str, Any]] = []
        self.consultations: Dict[str, DoctorConsultationRecord] = {}
        self.triage_alerts: List[Dict[str, Any]] = []
        self.seed_initial_demo_data()

    def seed_initial_demo_data(self):
        # Seed 1: Routine Cardiology & Diabetic Followup patient
        p1 = PatientDemographics(
            patient_id="P-101",
            name="Ramesh Kumar",
            age=58,
            gender="Male",
            phone="9876543210",
            abha_id="ramesh.kumar58@abdm",
            abha_number="91-4829-1029-4412",
            language="hi",
            token_number="OPD-A04"
        )
        c1 = DPDP2023Consent(
            consent_id="DPDP-SEED-01",
            patient_id=p1.patient_id,
            timestamp=datetime.now().isoformat(),
            consent_hash="9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
        )
        soc1 = SocratesResponse(
            site="Center of chest / epigastric region",
            onset="2 to 3 days ago",
            character="Dull aching pressure",
            radiation="No radiation",
            associations=["Mild fatigue"],
            timing="Intermittent",
            exacerbating_factors=["Exertion"],
            relieving_factors=["Rest"],
            severity_score=4
        )
        tr1 = TriageAlert(
            is_red_flag=False,
            triage_level=TriageLevel.GREEN,
            severity_score=4,
            detected_symptoms=["Dull chest heaviness on exertion"],
            clinical_rationale="Stable vitals, chronic diabetic follow-up.",
            recommended_action="Normal OPD queue allocation."
        )
        
        # Scanned doc 1 & 2
        doc1 = ocr_engine.process_document("rx_mukherjee.pdf", SAMPLE_DOCUMENTS[0]["preview_text"], p1.patient_id, "prescription")
        doc2 = ocr_engine.process_document("lab_report_aug.pdf", SAMPLE_DOCUMENTS[1]["preview_text"], p1.patient_id, "lab_report")

        sum1 = StructuredClinicalSummary(
            summary_id="SUM-SEED-01",
            patient_id=p1.patient_id,
            chief_complaint="Chest Heaviness & Diabetes Routine Review",
            duration_of_complaint="3 days",
            history_of_present_illness="58M presenting with intermittent dull chest pressure for 3 days on walking. Denies radiation, acute diaphoresis, or syncope. Known diabetic on oral hypoglycemic agents.",
            past_medical_history=["Type 2 Diabetes Mellitus (Uncontrolled)", "Essential Hypertension", "Dyslipidemia"],
            past_surgical_history=["None"],
            drug_allergies=["NKDA"],
            current_medications=doc1.extracted_medications,
            family_history=["Father died of MI at age 62"],
            personal_and_social_history={"Diet": "Vegetarian", "Smoking": "None", "Exercise": "Sedentary"},
            review_of_systems={"Cardiovascular": ["No syncope"], "Endocrine": ["Polydipsia, polyuria present"]},
            investigation_summary=doc2.extracted_investigations,
            triage=tr1,
            icd10_suggestions=[
                {"code": "E11.65", "title": "Type 2 diabetes mellitus with hyperglycemia"},
                {"code": "I20.9", "title": "Angina pectoris, unspecified"},
                {"code": "I10", "title": "Essential hypertension"}
            ],
            namaste_suggestions=[
                {"code": "NAM-AYU-PRM-01", "title": "Madhumeha (Diabetes)"}
            ]
        )

        sess1 = IntakeSession(
            session_id="SESS-101",
            patient=p1,
            consent=c1,
            chief_complaint="Chest Heaviness & Diabetes Checkup",
            affected_body_part="chest",
            socrates=soc1,
            documents=[doc1, doc2],
            triage=tr1,
            summary=sum1,
            is_completed=True
        )
        self.sessions[sess1.session_id] = sess1
        self.opd_queue.append({
            "token": p1.token_number,
            "session_id": sess1.session_id,
            "patient_id": p1.patient_id,
            "patient_name": p1.name,
            "age": p1.age,
            "gender": p1.gender,
            "chief_complaint": sess1.chief_complaint,
            "stream": p1.stream,
            "triage_level": tr1.triage_level,
            "is_red_flag": tr1.is_red_flag,
            "waiting_minutes": 8,
            "summary_id": sum1.summary_id,
            "has_scanned_docs": True,
            "created_at": datetime.now().isoformat()
        })

        # Seed 2: AYUSH Sandhigata Vata (Osteoarthritis) patient
        p2 = PatientDemographics(
            patient_id="P-102",
            name="Shanti Devi",
            age=52,
            gender="Female",
            phone="9812345678",
            abha_id="shanti.devi52@abdm",
            abha_number="91-5512-8821-9901",
            language="hi",
            stream="ayush",
            token_number="AYU-B12"
        )
        c2 = DPDP2023Consent(
            consent_id="DPDP-SEED-02",
            patient_id=p2.patient_id,
            timestamp=datetime.now().isoformat(),
            consent_hash="5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8"
        )
        doc_ayu = ocr_engine.process_document("ayush_opd.pdf", SAMPLE_DOCUMENTS[2]["preview_text"], p2.patient_id, "prescription")
        
        ayush_data = AyushPariksha(
            prakriti_scores={"vata": 54.0, "pitta": 30.0, "kapha": 16.0},
            dominant_prakriti="Vata Dominant (Pitta Anubandha)",
            agni="Manda Agni (Sluggish/Slow Digestion)",
            koshtha="Krura Koshtha (Hard/Costive - Vata)",
            sara="Madhyama Sara",
            samhanana="Madhyama",
            pramana="Madhyama",
            satmya="Madhyama Satmya",
            sattva="Madhyama Sattva",
            ahara_shakti="Moderate",
            vyayama_shakti="Avara (Reduced due to joint pain)",
            vaya="Madhyama Vaya",
            ahara_vihara_notes="High intake of sour & fermented food; late night sleeping; cold exposure exacerbates pain.",
            nidana_causative_factors=[
                "Vidahi Ahara Sevana (Excess sour/pungent food causing Amlapitta)",
                "Vata Prakopa Nidana (Cold climate and dry food aggravating Sandhi Vata)"
            ]
        )
        tr2 = TriageAlert(
            is_red_flag=False,
            triage_level=TriageLevel.GREEN,
            severity_score=5,
            detected_symptoms=["Bilateral Knee Pain (Sandhigata Vata)", "Hyperacidity (Amlapitta)"],
            clinical_rationale="Chronic degenerative joint disease with Pitta-Vata imbalance.",
            recommended_action="AYUSH Kayachikitsa & Panchakarma OPD."
        )
        sum2 = StructuredClinicalSummary(
            summary_id="SUM-SEED-02",
            patient_id=p2.patient_id,
            chief_complaint="Bilateral Knee Joint Pain & Acidity",
            duration_of_complaint="6 months",
            history_of_present_illness="52F presents with progressive bilateral knee stiffness and crepitus worse in cold weather and upon standing. Associated sour belching and sluggish digestion for 2 months.",
            past_medical_history=["Sandhigata Vata (Bilateral OA)", "Amlapitta (Hyperacidity)"],
            past_surgical_history=["None"],
            drug_allergies=["NKDA"],
            current_medications=doc_ayu.extracted_medications,
            ayush_assessment=ayush_data,
            investigation_summary=[],
            triage=tr2,
            icd10_suggestions=[{"code": "M17.0", "title": "Bilateral primary osteoarthritis of knee"}],
            namaste_suggestions=[
                {"code": "NAM-AYU-SND-01", "title": "Sandhigata Vata (Osteoarthritis)"},
                {"code": "NAM-AYU-AML-01", "title": "Amlapitta (Hyperacidity)"}
            ]
        )
        sess2 = IntakeSession(
            session_id="SESS-102",
            patient=p2,
            consent=c2,
            chief_complaint="Bilateral Knee Joint Pain & Acidity",
            affected_body_part="joints",
            ayush=ayush_data,
            documents=[doc_ayu],
            triage=tr2,
            summary=sum2,
            is_completed=True
        )
        self.sessions[sess2.session_id] = sess2
        self.opd_queue.append({
            "token": p2.token_number,
            "session_id": sess2.session_id,
            "patient_id": p2.patient_id,
            "patient_name": p2.name,
            "age": p2.age,
            "gender": p2.gender,
            "chief_complaint": sess2.chief_complaint,
            "stream": p2.stream,
            "triage_level": tr2.triage_level,
            "is_red_flag": tr2.is_red_flag,
            "waiting_minutes": 15,
            "summary_id": sum2.summary_id,
            "has_scanned_docs": True,
            "created_at": datetime.now().isoformat()
        })

db = InMemoryDB()
