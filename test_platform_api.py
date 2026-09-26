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
            # Verify name_en and name_hi are present
            first_complaint = data["complaints"][0]
            self.assertIn("name_en", first_complaint)
            self.assertIn("name_hi", first_complaint)
            self.assertIn("name", first_complaint)
        print("[OK] Multilingual Chief Complaints Passed (8 Indian Languages)")

    def test_03_socrates_guided_steps(self):
        for step in range(8):
            res = client.get(f"/api/v1/kiosk/socrates-step?step={step}&language=hi")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data["success"])
            self.assertIn("clinical_field", data["data"])
            self.assertIn("question", data["data"])
            # Ensure question contains multilingual translations and options contain label_en / label_hi
            self.assertIn("en", data["data"]["question"])
            self.assertIn("hi", data["data"]["question"])
            self.assertGreater(len(data["data"]["options"]), 0)
            self.assertIn("label_en", data["data"]["options"][0])
            self.assertIn("label_hi", data["data"]["options"][0])
        print("[OK] SOCRATES Step Navigation Passed (8 Steps with full Multilingual Schema)")

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
        ext = data["extracted"]
        # Verify top-level extracted fields and socrates_updates
        self.assertTrue("sweating" in str(ext).lower())
        self.assertIn("character", ext)
        self.assertIn("radiation", ext)
        self.assertIn("associations", ext)
        print("[OK] Vernacular Voice Parsing Engine Passed (Top-level & Nested fields)")

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

    def test_06_ayush_pariksha_scoring_and_questions(self):
        # 1. Test Questions Endpoint
        q_res = client.get("/api/v1/ayush/questions?language=hi")
        self.assertEqual(q_res.status_code, 200)
        q_data = q_res.json()
        self.assertTrue(q_data["success"])
        self.assertGreater(len(q_data["questions"]), 0)
        self.assertIn("title", q_data["questions"][0])
        self.assertIn("title_vernacular", q_data["questions"][0])
        self.assertTrue(q_data["questions"][0]["options"][0]["is_default"])

        # 2. Test Calculation with Aliases
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
        self.assertGreater(data["pariksha"]["prakriti_scores"]["vata"], 40.0)
        print("[OK] AYUSH Prakriti & Ashtavidha Pariksha Engine Passed (Questions & Scoring)")

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

    def test_09_custom_document_upload_ocr(self):
        # Test Custom Document OCR upload endpoint
        sess_res = client.post("/api/v1/kiosk/start-session", json={
            "name": "Priya Patel",
            "age": 42,
            "gender": "Female",
            "phone": "9823456789",
            "stream": "allopathy"
        })
        sess_id = sess_res.json()["session_id"]

        doc_res = client.post("/api/v1/documents/upload-ocr", data={
            "session_id": sess_id,
            "doc_type": "prescription",
            "filename": "custom_prescription.txt",
            "raw_text": "Rx: Tab Telma-H 40mg 1-0-0 x 30 days, Tab Glycomet-GP 2 500mg 1-0-1 before food. Fasting Blood Sugar: 188 mg/dL, HbA1c: 9.2%"
        })
        self.assertEqual(doc_res.status_code, 200)
        doc_data = doc_res.json()
        self.assertTrue(doc_data["success"])
        self.assertGreater(len(doc_data["document"]["extracted_medications"]), 0)
        self.assertGreater(len(doc_data["document"]["extracted_investigations"]), 0)
        print("[OK] Custom Document Upload & OCR Extraction Passed")

    def test_10_sql_relational_database_persistence(self):
        # 1. Test database diagnostics endpoint
        status_res = client.get("/api/v1/database/status")
        self.assertEqual(status_res.status_code, 200)
        status_data = status_res.json()
        self.assertTrue(status_data["success"])
        db_info = status_data["database"]
        self.assertEqual(db_info["engine"], "SQLite Relational Database")
        self.assertIn("patients", db_info["table_counts"])
        self.assertGreater(db_info["table_counts"]["patients"], 0)
        self.assertGreater(db_info["file_size_bytes"], 0)

        # 2. Test tables listing endpoint
        tables_res = client.get("/api/v1/database/tables")
        self.assertEqual(tables_res.status_code, 200)
        tables_data = tables_res.json()
        self.assertTrue(tables_data["success"])
        self.assertIn("intake_sessions", tables_data["tables"])

        # 3. Direct independent SQLite connection to verify disk file persistence
        import sqlite3
        from backend.app.core.config import settings

        conn = sqlite3.connect(settings.DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Verify tables and rows exist on disk
        cur.execute("SELECT COUNT(*) as cnt FROM patients")
        self.assertGreater(cur.fetchone()["cnt"], 0)

        cur.execute("SELECT COUNT(*) as cnt FROM intake_sessions")
        self.assertGreater(cur.fetchone()["cnt"], 0)

        cur.execute("SELECT COUNT(*) as cnt FROM opd_queue")
        self.assertGreater(cur.fetchone()["cnt"], 0)

        # Verify audit logs were written
        cur.execute("SELECT COUNT(*) as cnt FROM audit_logs")
        self.assertGreater(cur.fetchone()["cnt"], 0)

        conn.close()
        print("[OK] Relational SQL Database Persistence & Disk Integrity Passed")


if __name__ == "__main__":
    unittest.main()
