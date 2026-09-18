import re
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.app.models.schemas import ExtractedMedication, ExtractedLabInvestigation, DocumentDigitization

# Medical reference database for common Indian clinical tests
LAB_REFERENCE_RANGES = {
    "hba1c": {
        "name": "HbA1c (Glycated Hemoglobin)",
        "unit": "%",
        "min": 4.0,
        "max": 5.6,
        "critical_high": 9.0,
        "critical_low": 3.5
    },
    "fbs": {
        "name": "Fasting Blood Sugar (FBS)",
        "unit": "mg/dL",
        "min": 70.0,
        "max": 100.0,
        "critical_high": 250.0,
        "critical_low": 50.0
    },
    "ppbs": {
        "name": "Post-Prandial Blood Sugar (PPBS)",
        "unit": "mg/dL",
        "min": 80.0,
        "max": 140.0,
        "critical_high": 300.0,
        "critical_low": 60.0
    },
    "creatinine": {
        "name": "Serum Creatinine",
        "unit": "mg/dL",
        "min": 0.6,
        "max": 1.2,
        "critical_high": 2.5,
        "critical_low": 0.3
    },
    "hemoglobin": {
        "name": "Hemoglobin (Hb)",
        "unit": "g/dL",
        "min": 12.0,
        "max": 16.5,
        "critical_high": 19.0,
        "critical_low": 7.0
    },
    "tlc": {
        "name": "Total Leukocyte Count (TLC / WBC)",
        "unit": "/cumm",
        "min": 4000.0,
        "max": 11000.0,
        "critical_high": 20000.0,
        "critical_low": 2000.0
    },
    "cholesterol": {
        "name": "Total Serum Cholesterol",
        "unit": "mg/dL",
        "min": 125.0,
        "max": 200.0,
        "critical_high": 300.0,
        "critical_low": 90.0
    },
    "sgpt": {
        "name": "SGPT / ALT (Liver Function)",
        "unit": "U/L",
        "min": 10.0,
        "max": 45.0,
        "critical_high": 150.0,
        "critical_low": 0.0
    },
    "uric_acid": {
        "name": "Serum Uric Acid",
        "unit": "mg/dL",
        "min": 3.5,
        "max": 7.2,
        "critical_high": 10.0,
        "critical_low": 2.0
    },
    "tsh": {
        "name": "Thyroid Stimulating Hormone (TSH)",
        "unit": "uIU/mL",
        "min": 0.4,
        "max": 4.5,
        "critical_high": 15.0,
        "critical_low": 0.1
    }
}

# Indian Medical Brands and Common Prescriptions Database
KNOWN_DRUGS = [
    {"name": "Telma-H", "strength": "40/12.5mg", "form": "Tablet", "freq": "1-0-0", "timing": "After Breakfast", "dur": "30 days"},
    {"name": "Glycomet-GP 2", "strength": "500/2mg", "form": "Tablet", "freq": "1-0-1", "timing": "Before Meals", "dur": "30 days"},
    {"name": "Pan-D", "strength": "40/30mg", "form": "Capsule", "freq": "1-0-0", "timing": "Empty Stomach", "dur": "15 days"},
    {"name": "Rosuvas", "strength": "10mg", "form": "Tablet", "freq": "0-0-1", "timing": "At Bedtime", "dur": "30 days"},
    {"name": "Ecosprin", "strength": "75mg", "form": "Tablet", "freq": "0-1-0", "timing": "After Lunch", "dur": "30 days"},
    {"name": "Augmentin", "strength": "625mg", "form": "Tablet", "freq": "1-0-1", "timing": "After Food", "dur": "5 days"},
    {"name": "Thyronorm", "strength": "50mcg", "form": "Tablet", "freq": "1-0-0", "timing": "Early Morning Empty Stomach", "dur": "90 days"},
    {"name": "Amlong", "strength": "5mg", "form": "Tablet", "freq": "1-0-0", "timing": "Morning", "dur": "30 days"},
    {"name": "Met-XL", "strength": "25mg", "form": "Tablet", "freq": "1-0-0", "timing": "Morning", "dur": "30 days"},
    {"name": "Dolo 650", "strength": "650mg", "form": "Tablet", "freq": "1-1-1 SOS", "timing": "After Food", "dur": "3 days"},
    {"name": "Montek-LC", "strength": "10/5mg", "form": "Tablet", "freq": "0-0-1", "timing": "At Bedtime", "dur": "10 days"},
    {"name": "Ascoril-D", "strength": "100ml", "form": "Syrup", "freq": "2 tsp TID", "timing": "After Food", "dur": "5 days"},
    # Ayurvedic formulations
    {"name": "Arogyavardhini Vati", "strength": "250mg", "form": "Tablet", "freq": "2-0-2", "timing": "With Warm Water After Food", "dur": "30 days"},
    {"name": "Maharasnadi Kashayam", "strength": "200ml", "form": "Liquid Decoction", "freq": "15ml-0-15ml", "timing": "Before Meals with Equal Water", "dur": "21 days"},
    {"name": "Yogaraj Guggulu", "strength": "500mg", "form": "Tablet", "freq": "1-0-1", "timing": "After Food with Warm Water", "dur": "30 days"},
    {"name": "Triphala Churna", "strength": "5g", "form": "Powder", "freq": "0-0-1", "timing": "Bedtime with Lukewarm Water", "dur": "30 days"}
]

class OCREngine:
    @staticmethod
    def process_document(
        filename: str,
        text_content: Optional[str] = None,
        patient_id: str = "P-1001",
        doc_type: str = "prescription"
    ) -> DocumentDigitization:
        """
        Parses scanned prescription or lab report OCR text and structures it into clinical entities.
        """
        raw_text = text_content or ""
        doc_id = f"DOC-{int(datetime.now().timestamp()*1000)}"

        extracted_meds: List[ExtractedMedication] = []
        extracted_labs: List[ExtractedLabInvestigation] = []
        extracted_diagnoses: List[str] = []
        doc_date = None
        facility_name = "Government General Hospital / Private Clinic"

        # Detect Document Type from keywords if generic
        t_low = raw_text.lower()
        if any(w in t_low for w in ["blood", "serum", "pathology", "laboratory", "hba1c", "creatinine", "test report"]):
            doc_type = "lab_report"
        elif any(w in t_low for w in ["rx", "tab", "cap", "syrup", "dr.", "clinic", "dispensed"]):
            doc_type = "prescription"
        elif any(w in t_low for w in ["discharge", "admission", "discharge summary", "ot note"]):
            doc_type = "discharge_summary"

        # 1. Date Extraction
        date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', raw_text)
        if date_match:
            doc_date = date_match.group(1)
        else:
            doc_date = datetime.now().strftime("%d/%m/%Y")

        # 2. Extract Diagnoses
        diagnosis_patterns = [
            r'(?:Diagnosis|Dx|Impression|Known case of|K/C/O)[:\s]+([^\n\.]+)',
            r'(?:Type\s*2\s*Diabetes|T2DM|Hypertension|HTN|Dyslipidemia|GERD|Asthma|CAD|Osteoarthritis|Hypothyroidism)'
        ]
        for pat in diagnosis_patterns:
            matches = re.finditer(pat, raw_text, re.IGNORECASE)
            for m in matches:
                matched_val = m.group(0).strip()
                if len(matched_val) > 2 and matched_val not in extracted_diagnoses:
                    extracted_diagnoses.append(matched_val.replace("Diagnosis:", "").replace("Dx:", "").strip())

        # Fallback diagnosis keywords
        if "diabetes" in t_low or "sugar" in t_low or "glycomet" in t_low:
            if "Type 2 Diabetes Mellitus" not in extracted_diagnoses:
                extracted_diagnoses.append("Type 2 Diabetes Mellitus")
        if "hypertension" in t_low or "bp" in t_low or "telma" in t_low:
            if "Essential Hypertension" not in extracted_diagnoses:
                extracted_diagnoses.append("Essential Hypertension")
        if "joint" in t_low or "knee" in t_low or "arthritis" in t_low or "maharasnadi" in t_low:
            if "Osteoarthritis / Sandhigata Vata" not in extracted_diagnoses:
                extracted_diagnoses.append("Osteoarthritis (Sandhigata Vata)")
        if "chest pain" in t_low or "ecg" in t_low or "ecosprin" in t_low:
            if "Ischemic Heart Disease (CAD)" not in extracted_diagnoses:
                extracted_diagnoses.append("Ischemic Heart Disease (CAD)")

        # 3. Extract Medications
        for drug in KNOWN_DRUGS:
            if re.search(r'\b' + re.escape(drug["name"].lower()) + r'\b', t_low):
                # Search custom frequency in raw text near drug
                freq = drug["freq"]
                freq_match = re.search(r'\b(1-0-1|1-0-0|0-0-1|1-1-1|0-1-0|OD|BD|TID|TDS|HS)\b', raw_text, re.IGNORECASE)
                if freq_match:
                    freq = freq_match.group(1)

                extracted_meds.append(ExtractedMedication(
                    drug_name=drug["name"],
                    strength=drug["strength"],
                    dosage_form=drug["form"],
                    dosage_frequency=freq,
                    timing=drug["timing"],
                    duration=drug["dur"]
                ))

        # 4. Extract Lab Investigations
        # Search for HbA1c
        hba1c_match = re.search(r'(?:HbA1c|Glycated\s*Hb|Glycosylated\s*Hemoglobin)[\s:=]+([0-9]+\.?[0-9]*)', raw_text, re.IGNORECASE)
        if hba1c_match:
            val = float(hba1c_match.group(1))
            ref = LAB_REFERENCE_RANGES["hba1c"]
            flag = "NORMAL"
            is_abn = False
            if val >= ref["critical_high"]:
                flag = "CRITICAL HIGH"
                is_abn = True
            elif val > ref["max"]:
                flag = "HIGH"
                is_abn = True
            elif val < ref["min"]:
                flag = "LOW"
                is_abn = True
            extracted_labs.append(ExtractedLabInvestigation(
                test_name=ref["name"],
                measured_value=str(val),
                reference_range=f"{ref['min']} - {ref['max']}",
                unit=ref["unit"],
                is_abnormal=is_abn,
                flag=flag,
                test_date=doc_date
            ))

        # Search for Creatinine
        creat_match = re.search(r'(?:Creatinine|Serum\s*Creatinine|S\.\s*Creat)[\s:=]+([0-9]+\.?[0-9]*)', raw_text, re.IGNORECASE)
        if creat_match:
            val = float(creat_match.group(1))
            ref = LAB_REFERENCE_RANGES["creatinine"]
            flag = "NORMAL"
            is_abn = False
            if val >= ref["critical_high"]:
                flag = "CRITICAL HIGH"
                is_abn = True
            elif val > ref["max"]:
                flag = "HIGH"
                is_abn = True
            elif val < ref["min"]:
                flag = "LOW"
                is_abn = True
            extracted_labs.append(ExtractedLabInvestigation(
                test_name=ref["name"],
                measured_value=str(val),
                reference_range=f"{ref['min']} - {ref['max']}",
                unit=ref["unit"],
                is_abnormal=is_abn,
                flag=flag,
                test_date=doc_date
            ))

        # Search for Fasting Blood Sugar
        fbs_match = re.search(r'(?:Fasting\s*Blood\s*Sugar|FBS|Fasting\s*Glucose)[\s:=]+([0-9]+\.?[0-9]*)', raw_text, re.IGNORECASE)
        if fbs_match:
            val = float(fbs_match.group(1))
            ref = LAB_REFERENCE_RANGES["fbs"]
            flag = "HIGH" if val > ref["max"] else "LOW" if val < ref["min"] else "NORMAL"
            extracted_labs.append(ExtractedLabInvestigation(
                test_name=ref["name"],
                measured_value=str(val),
                reference_range=f"{ref['min']} - {ref['max']}",
                unit=ref["unit"],
                is_abnormal=(flag != "NORMAL"),
                flag=flag,
                test_date=doc_date
            ))

        # Search for Hemoglobin
        hb_match = re.search(r'(?:Hemoglobin|Hb|Hgb)[\s:=]+([0-9]+\.?[0-9]*)', raw_text, re.IGNORECASE)
        if hb_match:
            val = float(hb_match.group(1))
            ref = LAB_REFERENCE_RANGES["hemoglobin"]
            flag = "LOW" if val < ref["min"] else "HIGH" if val > ref["max"] else "NORMAL"
            extracted_labs.append(ExtractedLabInvestigation(
                test_name=ref["name"],
                measured_value=str(val),
                reference_range=f"{ref['min']} - {ref['max']}",
                unit=ref["unit"],
                is_abnormal=(flag != "NORMAL"),
                flag=flag,
                test_date=doc_date
            ))

        # Search for Total Cholesterol
        chol_match = re.search(r'(?:Cholesterol|Total\s*Cholesterol|Lipid\s*Cholesterol)[\s:=]+([0-9]+\.?[0-9]*)', raw_text, re.IGNORECASE)
        if chol_match:
            val = float(chol_match.group(1))
            ref = LAB_REFERENCE_RANGES["cholesterol"]
            flag = "HIGH" if val > ref["max"] else "NORMAL"
            extracted_labs.append(ExtractedLabInvestigation(
                test_name=ref["name"],
                measured_value=str(val),
                reference_range=f"{ref['min']} - {ref['max']}",
                unit=ref["unit"],
                is_abnormal=(flag != "NORMAL"),
                flag=flag,
                test_date=doc_date
            ))

        return DocumentDigitization(
            document_id=doc_id,
            patient_id=patient_id,
            document_type=doc_type,
            original_filename=filename,
            upload_timestamp=datetime.now().isoformat(),
            ocr_raw_text=raw_text,
            extracted_diagnoses=extracted_diagnoses,
            extracted_medications=extracted_meds,
            extracted_investigations=extracted_labs,
            historical_date=doc_date,
            doctor_or_facility=facility_name
        )

ocr_engine = OCREngine()
