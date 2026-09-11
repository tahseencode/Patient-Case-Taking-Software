"""
Sample Indian medical documents for 1-click OCR demonstration in MediKiosk.
"""

SAMPLE_DOCUMENTS = [
    {
        "id": "sample_rx_cardio_diabetic",
        "title": "Hospital OPD Prescription - Cardiology & Diabetes",
        "doc_type": "prescription",
        "date": "10/08/2026",
        "doctor": "Dr. S. K. Mukherjee, MD (Med), DM (Cardio)",
        "facility": "Apex Multi-Speciality Government Hospital, New Delhi",
        "preview_text": """
DR. S. K. MUKHERJEE, MD, DM (Cardiology)
Senior Consultant Cardiologist | Reg No: DMC-48291
Apex Government Hospital OPD - Room 104

Date: 10/08/2026
Patient: Ramesh Kumar | Age: 58 Yrs / Male | ABHA: 91-4829-1029-4412
Diagnosis / Known Case of:
- Essential Hypertension (Stage II)
- Type 2 Diabetes Mellitus (Uncontrolled)
- Dyslipidemia

Rx (Current Medications):
1. Tab Telma-H (Telmisartan 40mg + Hydrochlorothiazide 12.5mg)
   1-0-0 (Morning after breakfast) x 30 days
2. Tab Glycomet-GP 2 (Metformin 500mg + Glimepiride 2mg)
   1-0-1 (Before food) x 30 days
3. Tab Rosuvas 10mg (Rosuvastatin)
   0-0-1 (At bedtime) x 30 days
4. Tab Ecosprin 75mg (Aspirin)
   0-1-0 (After lunch) x 30 days
5. Cap Pan-D (Pantoprazole 40mg + Domperidone 30mg)
   1-0-0 (Empty stomach 30 mins before breakfast) x 15 days

Advice:
- Restrict salt < 5g/day. Diabetic diet chart given.
- Repeat HbA1c, Serum Creatinine, Lipid profile in 3 months.
- Review with fresh ECG if retrosternal chest pain occurs.
        """
    },
    {
        "id": "sample_lab_report_abnormal",
        "title": "NABL Accredited Pathology Lab - Comprehensive Metabolic & Diabetic Panel",
        "doc_type": "lab_report",
        "date": "12/08/2026",
        "doctor": "Dr. Ananya Roy, MD (Biochemistry)",
        "facility": "Central Diagnostic & Pathology Labs",
        "preview_text": """
CENTRAL DIAGNOSTIC & PATHOLOGY LABS (NABL ACCREDITED)
Department of Clinical Biochemistry & Hematology
Report ID: LAB-2026-88192 | Date of Collection: 12/08/2026
Patient: Ramesh Kumar | Age: 58 Y / Male | Ref Dr: Dr. S. K. Mukherjee

TEST NAME                              RESULT        UNIT         BIOLOGICAL REF RANGE
--------------------------------------------------------------------------------------
GLYCATED HEMOGLOBIN (HbA1c)             9.2 [CRITICAL] %          4.0 - 5.6 (Normal)
                                                                  5.7 - 6.4 (Prediabetes)
                                                                  > 6.5 (Diabetes)
ESTIMATED AVERAGE GLUCOSE (eAG)         217           mg/dL       90 - 120

FASTING BLOOD SUGAR (FBS)               188 [HIGH]    mg/dL       70 - 100
POST-PRANDIAL BLOOD SUGAR (PPBS)        274 [HIGH]    mg/dL       80 - 140

SERUM CREATININE                        1.9 [HIGH]    mg/dL       0.6 - 1.2
BLOOD UREA NITROGEN (BUN)               34  [HIGH]    mg/dL       7 - 20
SERUM URIC ACID                         7.8 [HIGH]    mg/dL       3.5 - 7.2

TOTAL SERUM CHOLESTEROL                 248 [HIGH]    mg/dL       125 - 200
TRIGLYCERIDES                           280 [HIGH]    mg/dL       < 150
HDL CHOLESTEROL (Good)                  36  [LOW]     mg/dL       40 - 60
LDL CHOLESTEROL (Calculated)            156 [HIGH]    mg/dL       < 100

HEMOGLOBIN (Hb)                         11.2 [LOW]    g/dL        12.0 - 16.5
TOTAL LEUKOCYTE COUNT (TLC)             8400          /cumm       4000 - 11000

INTERPRETATION:
Marked hyperglycemia with poorly controlled Glycated Hemoglobin (HbA1c 9.2%).
Early renal impairment noted with elevated Serum Creatinine (1.9 mg/dL).
Mixed dyslipidemia present. Clinical correlation and nephrology review advised.
        """
    },
    {
        "id": "sample_ayush_prescription",
        "title": "AYUSH Ayurvedic Hospital OPD Prescription - Sandhigata Vata & Amlapitta",
        "doc_type": "prescription",
        "date": "05/09/2026",
        "doctor": "Vaidya R. K. Shastri, BAMS, MD (Ayurveda - Kayachikitsa)",
        "facility": "National Institute of Ayurveda & Integrated AYUSH Centre",
        "preview_text": """
NATIONAL AYUSH RESEARCH HOSPITAL & INTEGRATED CARE CENTRE
Department of Kayachikitsa & Panchakarma
OPD Ticket No: AYU-2026-9041 | Date: 05/09/2026
Vaidya R. K. Shastri, MD (Ayurveda) | Reg: CCIM-61029

Rogi Name: Shanti Devi | Age: 52 Y / F | Prakriti: Vata-Pitta Dominant
Roga Pariksha / Diagnoses (NAMASTE AYUSH):
1. Sandhigata Vata (Bilateral Knee Osteoarthritis / Joint Degeneration) - Code: NAM-AYU-SND-01
2. Amlapitta / Vidagdhajirna (Hyperacidity & Sour Eructation) - Code: NAM-AYU-AML-01
3. Manda Agni & Krura Koshtha (Sluggish digestion & habitual constipation)

Chikitsa Sutra (Ayurvedic Prescriptions):
1. Tab Yogaraj Guggulu (500mg)
   1-0-1 (After food with warm water) x 30 days
2. Maharasnadi Kashayam (Liquid Decoction)
   15ml mixed with 15ml warm water, 1-0-1 (30 mins before meals) x 21 days
3. Tab Arogyavardhini Vati (250mg)
   1-0-1 (After lunch and dinner) x 15 days
4. Triphala Churna (5 grams)
   0-0-1 (Bedtime with lukewarm water) x 30 days
5. Mahanarayana Taila (For external Janu Basti / local knee massage)

Pathya-Apathya (Dietary & Lifestyle Advice):
- Pathya: Godhuma (Wheat), Mudga (Moong dal), Takra (Buttermilk with jeera), Warm water.
- Apathya: Strictly avoid excessively spicy, sour, fermented food, refrigerated ice water, and curd at night.
        """
    }
]
