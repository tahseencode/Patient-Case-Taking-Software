import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from backend.app.models.schemas import (
    PatientDemographics, SocratesResponse, AyushPariksha,
    DocumentDigitization, TriageAlert, StructuredClinicalSummary,
    ExtractedMedication, ExtractedLabInvestigation
)

# Standard ICD-10 and AYUSH NAMASTE mapping dictionary
ICD10_MAP = {
    "chest_pain": [
        {"code": "I20.9", "title": "Angina pectoris, unspecified (Ischemic Chest Pain)"},
        {"code": "I21.9", "title": "Acute myocardial infarction, unspecified (STEMI/NSTEMI)"},
        {"code": "R07.9", "title": "Chest pain, unspecified"}
    ],
    "breathlessness": [
        {"code": "R06.02", "title": "Shortness of breath / Dyspnea"},
        {"code": "J45.909", "title": "Unspecified asthma, uncomplicated"},
        {"code": "I50.9", "title": "Heart failure, unspecified"}
    ],
    "fever": [
        {"code": "R50.9", "title": "Fever, unspecified (Pyrexia of Unknown Origin)"},
        {"code": "A01.0", "title": "Typhoid fever"},
        {"code": "A90", "title": "Dengue fever"}
    ],
    "diabetes_followup": [
        {"code": "E11.9", "title": "Type 2 diabetes mellitus without complications"},
        {"code": "E11.65", "title": "Type 2 diabetes mellitus with hyperglycemia"},
        {"code": "I10", "title": "Essential (primary) hypertension"}
    ],
    "joint_pain": [
        {"code": "M17.9", "title": "Osteoarthritis of knee, unspecified"},
        {"code": "M54.5", "title": "Low back pain"},
        {"code": "M06.9", "title": "Rheumatoid arthritis, unspecified"}
    ],
    "abdominal_pain": [
        {"code": "R10.9", "title": "Abdominal pain, unspecified"},
        {"code": "K21.9", "title": "Gastro-esophageal reflux disease (GERD)"},
        {"code": "K29.7", "title": "Gastritis, unspecified"}
    ],
    "headache_dizziness": [
        {"code": "G43.909", "title": "Migraine, unspecified"},
        {"code": "R42", "title": "Dizziness and giddiness"},
        {"code": "I63.9", "title": "Cerebral infarction, unspecified"}
    ]
}

NAMASTE_MAP = {
    "chest_pain": [
        {"code": "NAM-AYU-HRD-01", "title": "Hritshula / Vataja Hridroga (Cardiac chest pain)"},
        {"code": "NAM-AYU-URAS-02", "title": "Urah-Kshata (Chest discomfort)"}
    ],
    "joint_pain": [
        {"code": "NAM-AYU-SND-01", "title": "Sandhigata Vata (Osteoarthritis of joints)"},
        {"code": "NAM-AYU-AMA-02", "title": "Amavata (Rheumatoid arthritis / systemic inflammatory)"},
        {"code": "NAM-AYU-KTI-03", "title": "Katigraha / Gridhrasi (Lumbago / Sciatica)"}
    ],
    "diabetes_followup": [
        {"code": "NAM-AYU-PRM-01", "title": "Madhumeha / Vataja Prameha (Type 2 Diabetes Mellitus)"},
        {"code": "NAM-AYU-MDH-02", "title": "Medoroga / Sthaulya (Metabolic syndrome & obesity)"}
    ],
    "abdominal_pain": [
        {"code": "NAM-AYU-AML-01", "title": "Amlapitta (Hyperacidity / GERD)"},
        {"code": "NAM-AYU-SHL-02", "title": "Parinama Shula / Annadrava Shula (Gastric & Peptic discomfort)"},
        {"code": "NAM-AYU-GRA-03", "title": "Grahani Dosha (Malabsorption / IBS)"}
    ],
    "fever": [
        {"code": "NAM-AYU-JVR-01", "title": "Vata-Kaphaja Jvara (Acute viral pyrexia)"},
        {"code": "NAM-AYU-TAR-02", "title": "Taruna Jvara (Acute onset febrile illness)"}
    ]
}

class ClinicalSummarizer:
    @staticmethod
    def generate_summary(
        patient: PatientDemographics,
        chief_complaint_id: str,
        chief_complaint_title: str,
        socrates: SocratesResponse,
        documents: List[DocumentDigitization],
        triage: TriageAlert,
        ayush: Optional[AyushPariksha] = None
    ) -> StructuredClinicalSummary:
        summary_id = f"SUM-{uuid.uuid4().hex[:8].upper()}"

        # 1. Synthesize HPI Narrative
        hpi_parts = []
        onset_str = socrates.onset or "acute duration"
        site_str = socrates.site or "affected region"
        char_str = socrates.character or "discomfort"
        
        hpi_parts.append(
            f"The patient, a {patient.age}-year-old {patient.gender.lower()}, presents with complaints of {chief_complaint_title.lower()} "
            f"situated at the {site_str}. "
            f"The onset was described as {onset_str}, characterized by {char_str}."
        )

        if socrates.radiation and "no" not in socrates.radiation.lower():
            hpi_parts.append(f"Pain exhibits radiation towards {socrates.radiation}.")

        if socrates.associations:
            hpi_parts.append(f"Associated symptoms include {', '.join(socrates.associations)}.")

        if socrates.timing:
            hpi_parts.append(f"Temporal pattern is noted to be {socrates.timing}.")

        if socrates.exacerbating_factors or socrates.relieving_factors:
            ex = f"exacerbated by {', '.join(socrates.exacerbating_factors)}" if socrates.exacerbating_factors else ""
            rel = f"relieved by {', '.join(socrates.relieving_factors)}" if socrates.relieving_factors else ""
            hpi_parts.append(f"Symptoms are {ex}{' and ' if (ex and rel) else ''}{rel}.")

        hpi_parts.append(f"Current self-reported pain/severity score is {socrates.severity_score or 5}/10.")
        hpi_narrative = " ".join(hpi_parts)

        # 2. Extract medications and past diagnoses from scanned documents
        all_meds: List[ExtractedMedication] = []
        all_labs: List[ExtractedLabInvestigation] = []
        past_medical: List[str] = []

        for doc in documents:
            for m in doc.extracted_medications:
                if not any(existing.drug_name == m.drug_name for existing in all_meds):
                    all_meds.append(m)
            for lab in doc.extracted_investigations:
                all_labs.append(lab)
            for dx in doc.extracted_diagnoses:
                if dx not in past_medical:
                    past_medical.append(dx)

        if not past_medical and "diabetes" in chief_complaint_id:
            past_medical.append("Type 2 Diabetes Mellitus (Known)")

        # 3. Code Suggestions
        icd_codes = ICD10_MAP.get(chief_complaint_id, [
            {"code": "R69", "title": "Illness, unspecified"}
        ])
        namaste_codes = NAMASTE_MAP.get(chief_complaint_id, [
            {"code": "NAM-AYU-GEN-01", "title": "Samanya Vyadhi (General Systemic Condition)"}
        ])

        # 4. Review of Systems
        ros = {
            "Cardiovascular": ["No history of syncope" if not any("faint" in str(a).lower() for a in (socrates.associations or [])) else "Positive for dizziness/presyncope"],
            "Respiratory": ["Dyspnea noted" if any("breath" in str(a).lower() for a in (socrates.associations or [])) else "Denies wheezing/hemoptysis"],
            "Gastrointestinal": ["Nausea/Vomiting present" if any("vomit" in str(a).lower() for a in (socrates.associations or [])) else "Appetite preserved"],
            "Musculoskeletal": ["Joint pain reported" if "joint" in chief_complaint_id else "No limb weakness noted"]
        }

        return StructuredClinicalSummary(
            summary_id=summary_id,
            patient_id=patient.patient_id,
            chief_complaint=chief_complaint_title,
            duration_of_complaint=socrates.onset or "Recent days",
            history_of_present_illness=hpi_narrative,
            past_medical_history=past_medical or ["No prior chronic conditions recorded"],
            past_surgical_history=["None reported"],
            drug_allergies=["NKDA (No Known Drug Allergies)"],
            current_medications=all_meds,
            family_history=["Family history of hypertension / diabetes" if patient.age > 45 else "Non-contributory"],
            personal_and_social_history={
                "Diet": "Mixed Indian Diet",
                "Smoking/Tobacco": "Non-smoker",
                "Alcohol": "Occasional/None",
                "Sleep": "6-7 hours/night"
            },
            review_of_systems=ros,
            ayush_assessment=ayush,
            investigation_summary=all_labs,
            triage=triage,
            icd10_suggestions=icd_codes,
            namaste_suggestions=namaste_codes,
            summary_generated_at=datetime.now().isoformat(),
            physician_reviewed=False,
            physician_notes=None
        )

clinical_summarizer = ClinicalSummarizer()
