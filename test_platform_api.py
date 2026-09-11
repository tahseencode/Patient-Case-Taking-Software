"""
Automated Test Suite for MediKiosk & AyurKiosk Platform (SIH26047)
Validates all API endpoints, models, OCR processing, SOCRATES dialogue,
Prakriti calculation, OPD queue, and ABDM FHIR R4 Bundle generation.
"""

import sys
import unittest
from fastapi.testclient import TestClient
from backend.main import app
from backend.app.database.db import db

client = TestClient(app)

class TestMediKioskPlatform(unittest.TestCase):
    
    def test_01_health_and_root(self):
        res = client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "online")
        self.assertIn("IN-AIIMS-DELHI-0012", data["facility_id"])
        print("[OK] Health Check Passed")

    def test_02_kiosk_complaints_multilingual(self):
        for lang in ["en", "hi", "mr", "ta", "te", "bn", "gu", "kn"]:
            res = client.get(f"/api/v1/kiosk/complaints?language={lang}")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data["success"])
            self.assertGreater(len(data["complaints"]), 0)
        print("[OK] Multilingual Chief Complaints Passed (8 Indian Languages)")

    def test_03_socrates_guided_steps(self):
        for step in range(8):
            res = client.get(f"/api/v1/kiosk/socrates-step?step={step}&language=hi")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data["success"])
            self.assertIn("clinical_field", data["data"])
        print("[OK] SOCRATES Step Navigation Passed")

    def test_04_voice_parsing_engine(self):
        res = client.post("/api/v1/kiosk/parse-voice", json={
            "transcript": "मुझे कल रात से छाती में बहुत तेज़ जकड़न और भारीपन लग रहा है जो बाएं हाथ तक जा रहा है और पसीना आ रहा है",
            "chief_complaint_id": "chest_pain",
            "language": "hi"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("extracted", data)
        self.assertTrue("sweating" in str(data["extracted"]).lower())
        print("[OK] Vernacular Voice Parsing Engine Passed")

    def test_05_kiosk_full_intake_flow(self):
        # 1. Start Session
        start_res = client.post("/api/v1/kiosk/start-session", json={
            "name": "Amitabh Sharma",
            "age": 62,
            "gender": "Male",
            "phone": "9811122233",
            "abha_id": "amitabh.sharma62@abdm",
            "language": "hi",
            "stream": "allopathy",
            "voice_consent": True,
            "ocr_consent": True,
            "abha_consent": True
        })
        self.assertEqual(start_res.status_code, 200)
        sess_data = start_res.json()
        session_id = sess_data["session_id"]
        self.assertTrue(sess_data["success"])

        # 2. Submit SOCRATES with Red-Flag Trigger
        soc_res = client.post("/api/v1/kiosk/submit-socrates", json={
            "session_id": session_id,
            "chief_complaint_id": "chest_pain",
            "chief_complaint_title": "Chest Pain / Discomfort",
            "affected_body_part": "chest",
            "socrates": {
                "site": "Center of chest",
                "onset": "Within last 2 hours",
                "character": "Heavy crushing pressure",
                "radiation": "Spreads to Left Arm, Shoulder or Jaw",
                "associations": ["Profuse Sweating", "Acute Dyspnea"],
                "timing": "Continuous",
                "exacerbating_factors": ["Walking"],
                "relieving_factors": ["None"],
                "severity_score": 9
            }
        })
        self.assertEqual(soc_res.status_code, 200)
        soc_data = soc_res.json()
        self.assertTrue(soc_data["triage"]["is_red_flag"])
        self.assertEqual(soc_data["triage"]["triage_level"], "emergency")

        # 3. Load Sample OCR Document
        ocr_res = client.post("/api/v1/documents/load-sample", json={
            "session_id": session_id,
            "sample_id": "sample_rx_cardio_diabetic"
        })
        self.assertEqual(ocr_res.status_code, 200)
        doc_data = ocr_res.json()
        self.assertTrue(doc_data["success"])
        self.assertGreater(len(doc_data["document"]["extracted_medications"]), 0)

        # 4. Finalize Intake & Issue Token
        fin_res = client.post("/api/v1/kiosk/finalize-intake", json={
            "session_id": session_id
        })
        self.assertEqual(fin_res.status_code, 200)
        fin_data = fin_res.json()
        self.assertTrue(fin_data["success"])
        self.assertIsNotNone(fin_data["summary"])
        self.assertIn("OPD", fin_data["token_number"])
        print(f"[OK] Kiosk Full Intake & Red-Flag Triage Passed (Token: {fin_data['token_number']})")

    def test_06_ayush_pariksha_scoring(self):
        res = client.post("/api/v1/ayush/calculate-pariksha", json={
            "answers": {
                "body_frame": "lean_thin",
                "skin_texture": "dry_rough",
                "appetite_level": "irregular",
                "sleep_quality": "interrupted",
                "bowel_habit": "hard_dry"
            },
            "lifestyle_notes": "Late night study, cold water consumption",
            "language": "hi"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        self.assertIn("Vata", data["pariksha"]["dominant_prakriti"])
        print("[OK] AYUSH Prakriti & Ashtavidha Pariksha Engine Passed")

    def test_07_doctor_queue_and_consultation(self):
        # Fetch queue
        q_res = client.get("/api/v1/doctor/opd-queue")
        self.assertEqual(q_res.status_code, 200)
        queue = q_res.json()["queue"]
        self.assertGreater(len(queue), 0)
        test_session = queue[0]["session_id"]

        # Fetch Deep Patient Summary
        sum_res = client.get(f"/api/v1/doctor/patient-summary/{test_session}")
        self.assertEqual(sum_res.status_code, 200)
        sum_data = sum_res.json()
        self.assertTrue(sum_data["success"])

        # Prescribe & Complete Consultation
        comp_res = client.post("/api/v1/doctor/prescribe-and-complete", json={
            "session_id": test_session,
            "doctor_name": "Dr. S. K. Mukherjee, MD",
            "doctor_department": "Cardiology OPD",
            "diagnosis": "Unstable Angina Pectoris (I20.0)",
            "icd10_code": "I20.0",
            "clinical_notes": "Stat Aspirin and Clopidogrel loaded. Emergency ECG taken.",
            "prescriptions": [
                {
                    "medicine_name": "Tab Sorbitrate 5mg",
                    "dosage": "5mg",
                    "frequency": "Sublingually PRN",
                    "duration": "5 days",
                    "instructions": "Place under tongue if chest tightness recurs"
                }
            ],
            "ordered_investigations": ["Emergency Troponin I", "12-Lead ECG", "2D Echo"],
            "follow_up_date": "Emergency Ward Admission"
        })
        self.assertEqual(comp_res.status_code, 200)
        comp_data = comp_res.json()
        self.assertTrue(comp_data["success"])
        self.assertIsNotNone(comp_data["fhir_bundle"])
        print("[OK] Doctor Consultation & ABDM FHIR Bundle Generation Passed")

    def test_08_abdm_fhir_and_dpdp(self):
        # Verify Provisional ABHA
        abha_res = client.post("/api/v1/abdm/verify-abha", json={"abha_input": "91-4829-1029-4412"})
        self.assertEqual(abha_res.status_code, 200)
        self.assertTrue(abha_res.json()["is_verified"])

        # Hospital Throughput Stats
        stats_res = client.get("/api/v1/abdm/hospital-stats")
        self.assertEqual(stats_res.status_code, 200)
        stats = stats_res.json()["metrics"]
        self.assertGreater(stats["clinical_time_saved_percentage"], 80)
        print("[OK] ABDM Ecosystem & Hospital Analytics Passed")


if __name__ == "__main__":
    unittest.main()
