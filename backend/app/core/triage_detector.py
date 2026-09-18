from typing import List, Dict, Any, Optional
from backend.app.models.schemas import TriageAlert, TriageLevel, SocratesResponse

class TriageDetector:
    @staticmethod
    def evaluate_triage(
        chief_complaint_id: Optional[str],
        socrates: SocratesResponse,
        voice_keywords: Optional[List[str]] = None,
        age: Optional[int] = None
    ) -> TriageAlert:
        detected_symptoms = []
        is_red = False
        is_yellow = False
        rationale_parts = []
        severity = socrates.severity_score or 5

        # 1. Check Cardiac / Acute Coronary Syndrome (ACS) Red-Flags
        is_chest = chief_complaint_id in ["chest_pain", "breathlessness"] or (socrates.site and "chest" in socrates.site.lower())
        has_radiation = socrates.radiation and ("arm" in socrates.radiation.lower() or "jaw" in socrates.radiation.lower())
        has_sweating = any("sweat" in str(a).lower() for a in (socrates.associations or []))
        has_dyspnea = any("breath" in str(a).lower() or "short" in str(a).lower() for a in (socrates.associations or []))
        has_heavy = socrates.character and ("heavy" in socrates.character.lower() or "crush" in socrates.character.lower() or "tight" in socrates.character.lower())

        if is_chest and (has_radiation or (has_sweating and has_dyspnea) or (has_heavy and severity >= 7)):
            is_red = True
            detected_symptoms.extend(["Acute Chest Discomfort", "Radiation to Left Arm/Jaw", "Diaphoresis/Sweating", "Dyspnea"])
            rationale_parts.append("CRITICAL: High clinical probability of Acute Coronary Syndrome (STEMI / NSTEMI).")

        # 2. Check Acute Stroke / Neurological Emergency
        is_neuro = chief_complaint_id == "headache_dizziness"
        if is_neuro and (severity >= 8 or (socrates.onset and "sudden" in socrates.onset.lower())):
            is_red = True
            detected_symptoms.extend(["Thunderclap Headache", "Sudden Neurological Deficit / Dizziness"])
            rationale_parts.append("CRITICAL: Suspected Acute Stroke / Subarachnoid Hemorrhage.")

        # 3. Check Severe Respiratory Distress
        if chief_complaint_id == "breathlessness" and (severity >= 8 or has_sweating):
            is_red = True
            detected_symptoms.extend(["Severe Respiratory Distress", "Hypoxia Risk"])
            rationale_parts.append("CRITICAL: Impending respiratory failure or acute pulmonary edema.")

        # 4. Check Acute Abdomen
        if chief_complaint_id == "abdominal_pain" and severity >= 9 and socrates.onset and "sudden" in socrates.onset.lower():
            is_red = True
            detected_symptoms.extend(["Acute Severe Abdominal Pain (10/10)", "Possible Perforation / Obstruction"])
            rationale_parts.append("CRITICAL: Acute Surgical Abdomen requiring immediate surgeon evaluation.")

        # 5. Check Priority (Yellow) Flags if not Red
        if not is_red:
            if severity >= 7:
                is_yellow = True
                detected_symptoms.append(f"Severe Pain Score ({severity}/10)")
                rationale_parts.append("High severity symptom requiring expedited OPD triage.")
            elif chief_complaint_id == "fever" and any("chill" in str(a).lower() or "faint" in str(a).lower() for a in (socrates.associations or [])):
                is_yellow = True
                detected_symptoms.append("High Grade Febrile Episode with Systemic Chills")
                rationale_parts.append("Febrile illness requiring early vitals and blood work.")
            elif chief_complaint_id in ["chest_pain", "breathlessness"]:
                is_yellow = True
                detected_symptoms.append("Cardiorespiratory Symptom (Moderate)")
                rationale_parts.append("Priority cardiorespiratory evaluation.")

        # Determine Final Level and Recommended Action
        if is_red:
            triage_level = TriageLevel.RED
            action = "EMERGENCY: Immediate redirection to Red Resuscitation Bay / Emergency Room (Stat ECG & Vitals)"
            rationale = " ".join(rationale_parts)
            calculated_score = max(severity, 9)
        elif is_yellow:
            triage_level = TriageLevel.YELLOW
            action = "PRIORITY: Fast-track queue in Yellow OPD triage desk within 15 minutes."
            rationale = " ".join(rationale_parts) if rationale_parts else "Moderate-to-high risk profile warranting priority assessment."
            calculated_score = max(severity, 6)
        else:
            triage_level = TriageLevel.GREEN
            action = "ROUTINE: Normal OPD queue allocation with AI pre-consultation summary."
            rationale = "Stable clinical parameters without emergency red-flags."
            calculated_score = min(severity, 4)

        return TriageAlert(
            is_red_flag=is_red,
            triage_level=triage_level,
            severity_score=calculated_score,
            detected_symptoms=list(set(detected_symptoms)),
            clinical_rationale=rationale,
            recommended_action=action
        )

triage_detector = TriageDetector()
