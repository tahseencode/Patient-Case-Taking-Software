"""
MediKiosk & AyurKiosk - SQL Relational Database Engine
SIH26047: AI-Powered Digital Clinical Intake Platform
Standards: ABDM FHIR R4, DPDP Act 2023, ICD-10, AYUSH NAMASTE

This module provides a production-grade, thread-safe SQLite implementation
with full schema initialization, persistence, foreign key enforcement, WAL mode,
audit logging, and backwards-compatible proxies for seamless API integration.
"""

import os
import json
import sqlite3
import threading
from datetime import datetime
from contextlib import contextmanager
from typing import Dict, List, Optional, Any

from backend.app.core.config import settings
from backend.app.models.schemas import (
    PatientDemographics, DPDP2023Consent, SocratesResponse,
    AyushPariksha, TriageAlert, TriageLevel,
    StructuredClinicalSummary, DoctorConsultationRecord,
    ExtractedMedication, ExtractedLabInvestigation, DocumentDigitization,
    DoctorPrescriptionItem, IntakeSession, LanguageEnum, StreamEnum
)
from backend.app.core.ocr_engine import ocr_engine
from backend.app.sample_data.sample_documents import SAMPLE_DOCUMENTS


def _to_jsonable(obj: Any) -> Any:
    """Recursively converts Pydantic models, Enums, and structures into JSON-serializable primitives."""
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        return _to_jsonable(obj.model_dump())
    if hasattr(obj, "dict"):
        return _to_jsonable(obj.dict())
    if isinstance(obj, list):
        return [_to_jsonable(item) for item in obj]
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if hasattr(obj, "value"):
        return obj.value
    return obj


def _json_dumps(obj: Any) -> str:
    """Helper to serialize complex data/models to JSON string."""
    if obj is None:
        return ""
    return json.dumps(_to_jsonable(obj), default=str)


def _json_loads(data: Optional[str], default: Any = None) -> Any:
    """Helper to safely parse JSON strings from SQLite."""
    if not data or data.strip() == "":
        return default
    try:
        return json.loads(data)
    except Exception:
        return default


class SQLDatabase:
    """
    High-level, thread-safe relational database manager.
    Connects to the SQLite database file specified in Settings.
    """

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.DATABASE_PATH
        self._lock = threading.RLock()
        
        # Ensure database directory exists
        db_dir = os.path.dirname(os.path.abspath(self.db_path))
        os.makedirs(db_dir, exist_ok=True)

        # Initialize schema and seed demo data if fresh
        self.init_schema()
        self._check_and_seed()

        # Proxies for seamless drop-in backwards compatibility with InMemoryDB
        self.sessions = SessionsProxy(self)
        self._opd_queue = OPDQueueProxy(self)
        self.consultations = ConsultationsProxy(self)
        self.triage_alerts = TriageAlertsProxy(self)

    @property
    def opd_queue(self):
        return self._opd_queue

    @opd_queue.setter
    def opd_queue(self, new_queue: List[Dict[str, Any]]):
        with self._lock:
            current_sids = {q.get("session_id") for q in self._opd_queue if q.get("session_id")}
            new_sids = {q.get("session_id") for q in new_queue if q.get("session_id")}
            removed_sids = current_sids - new_sids
            for sid in removed_sids:
                self.complete_opd_queue_item(sid)
            self._opd_queue.reload()

    @contextmanager
    def get_connection(self):
        """Context manager providing thread-safe, WAL-enabled SQLite connection."""
        conn = sqlite3.connect(self.db_path, check_same_thread=False, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.execute("PRAGMA journal_mode = WAL;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_schema(self):
        """Executes the DDL statements from schema.sql to ensure all tables exist."""
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        if not os.path.exists(schema_path):
            raise FileNotFoundError(f"schema.sql not found at {schema_path}")

        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        with self._lock:
            with self.get_connection() as conn:
                conn.executescript(schema_sql)

    def _check_and_seed(self):
        """Seeds demo data if the patients table is empty."""
        with self._lock:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM patients")
                row = cursor.fetchone()
                if row and row["count"] == 0:
                    self.seed_initial_demo_data()

    # --------------------------------------------------------------------------
    # PATIENT CRUD
    # --------------------------------------------------------------------------
    def save_patient(self, p: PatientDemographics):
        with self._lock:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO patients (
                        patient_id, name, age, gender, phone,
                        abha_id, abha_number, language, stream,
                        token_number, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(patient_id) DO UPDATE SET
                        name=excluded.name,
                        age=excluded.age,
                        gender=excluded.gender,
                        phone=excluded.phone,
                        abha_id=excluded.abha_id,
                        abha_number=excluded.abha_number,
                        language=excluded.language,
                        stream=excluded.stream,
                        token_number=excluded.token_number;
                """, (
                    p.patient_id, p.name, p.age, p.gender, p.phone,
                    p.abha_id, p.abha_number,
                    p.language.value if hasattr(p.language, "value") else str(p.language),
                    p.stream.value if hasattr(p.stream, "value") else str(p.stream),
                    p.token_number, p.created_at
                ))

    def get_patient(self, patient_id: str) -> Optional[PatientDemographics]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return PatientDemographics(
                patient_id=row["patient_id"],
                name=row["name"],
                age=row["age"],
                gender=row["gender"],
                phone=row["phone"],
                abha_id=row["abha_id"],
                abha_number=row["abha_number"],
                language=LanguageEnum(row["language"]) if row["language"] in [e.value for e in LanguageEnum] else LanguageEnum.HI,
                stream=StreamEnum(row["stream"]) if row["stream"] in [e.value for e in StreamEnum] else StreamEnum.ALLOPATHY,
                token_number=row["token_number"],
                created_at=row["created_at"]
            )

    # --------------------------------------------------------------------------
    # CONSENT CRUD (DPDP 2023)
    # --------------------------------------------------------------------------
    def save_consent(self, c: DPDP2023Consent):
        with self._lock:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO consents (
                        consent_id, patient_id, timestamp,
                        voice_capture_allowed, ocr_processing_allowed,
                        abha_data_sharing_allowed, anonymized_research_allowed,
                        consent_version, audio_consent_verified, consent_hash
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(consent_id) DO UPDATE SET
                        voice_capture_allowed=excluded.voice_capture_allowed,
                        ocr_processing_allowed=excluded.ocr_processing_allowed,
                        abha_data_sharing_allowed=excluded.abha_data_sharing_allowed,
                        anonymized_research_allowed=excluded.anonymized_research_allowed,
                        consent_hash=excluded.consent_hash;
                """, (
                    c.consent_id, c.patient_id, c.timestamp,
                    1 if c.voice_capture_allowed else 0,
                    1 if c.ocr_processing_allowed else 0,
                    1 if c.abha_data_sharing_allowed else 0,
                    1 if c.anonymized_research_allowed else 0,
                    c.consent_version,
                    1 if c.audio_consent_verified else 0,
                    c.consent_hash
                ))

    def get_consent(self, consent_id: str) -> Optional[DPDP2023Consent]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM consents WHERE consent_id = ?", (consent_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return DPDP2023Consent(
                consent_id=row["consent_id"],
                patient_id=row["patient_id"],
                timestamp=row["timestamp"],
                voice_capture_allowed=bool(row["voice_capture_allowed"]),
                ocr_processing_allowed=bool(row["ocr_processing_allowed"]),
                abha_data_sharing_allowed=bool(row["abha_data_sharing_allowed"]),
                anonymized_research_allowed=bool(row["anonymized_research_allowed"]),
                consent_version=row["consent_version"],
                audio_consent_verified=bool(row["audio_consent_verified"]),
                consent_hash=row["consent_hash"]
            )

    # --------------------------------------------------------------------------
    # INTAKE SESSION & CLINICAL SUMMARY CRUD
    # --------------------------------------------------------------------------
    def save_session(self, sess: IntakeSession):
        with self._lock:
            # 1. Ensure Patient & Consent are saved
            self.save_patient(sess.patient)
            self.save_consent(sess.consent)

            now_iso = datetime.now().isoformat()
            socrates_json = _json_dumps(sess.socrates) if sess.socrates else None
            ayush_json = _json_dumps(sess.ayush) if sess.ayush else None
            triage_json = _json_dumps(sess.triage) if sess.triage else None

            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO intake_sessions (
                        session_id, patient_id, consent_id,
                        chief_complaint, affected_body_part,
                        socrates_data, ayush_data, triage_data,
                        is_completed, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        chief_complaint=excluded.chief_complaint,
                        affected_body_part=excluded.affected_body_part,
                        socrates_data=excluded.socrates_data,
                        ayush_data=excluded.ayush_data,
                        triage_data=excluded.triage_data,
                        is_completed=excluded.is_completed,
                        updated_at=excluded.updated_at;
                """, (
                    sess.session_id, sess.patient.patient_id, sess.consent.consent_id,
                    sess.chief_complaint, sess.affected_body_part,
                    socrates_json, ayush_json, triage_json,
                    1 if sess.is_completed else 0,
                    now_iso, now_iso
                ))

            # 2. Save Clinical Summary if present
            if sess.summary:
                self.save_clinical_summary(sess.session_id, sess.summary)

            # 3. Save any attached digitized documents
            if sess.documents:
                for doc in sess.documents:
                    self.save_document(sess.session_id, doc)

            # 4. Record audit event
            self.log_audit("SAVE_SESSION", patient_id=sess.patient.patient_id, session_id=sess.session_id)

    def get_session(self, session_id: str) -> Optional[IntakeSession]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM intake_sessions WHERE session_id = ?", (session_id,))
            s_row = cursor.fetchone()
            if not s_row:
                return None

        patient = self.get_patient(s_row["patient_id"])
        consent = self.get_consent(s_row["consent_id"])
        if not patient or not consent:
            return None

        # Reconstruct SocratesResponse
        socrates_raw = _json_loads(s_row["socrates_data"], {})
        socrates = SocratesResponse(**socrates_raw) if socrates_raw else SocratesResponse()

        # Reconstruct AyushPariksha
        ayush_raw = _json_loads(s_row["ayush_data"])
        ayush = AyushPariksha(**ayush_raw) if ayush_raw else None

        # Reconstruct TriageAlert
        triage_raw = _json_loads(s_row["triage_data"], {})
        triage = TriageAlert(**triage_raw) if triage_raw else TriageAlert()

        # Load Summary and Documents
        summary = self.get_clinical_summary(session_id)
        documents = self.get_session_documents(session_id)

        return IntakeSession(
            session_id=s_row["session_id"],
            patient=patient,
            consent=consent,
            chief_complaint=s_row["chief_complaint"],
            affected_body_part=s_row["affected_body_part"],
            socrates=socrates,
            ayush=ayush,
            documents=documents,
            triage=triage,
            summary=summary,
            is_completed=bool(s_row["is_completed"])
        )

    def session_exists(self, session_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM intake_sessions WHERE session_id = ?", (session_id,))
            return cursor.fetchone() is not None

    def count_sessions(self) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) as count FROM intake_sessions")
            row = cursor.fetchone()
            return row["count"] if row else 0

    def get_all_sessions(self) -> Dict[str, IntakeSession]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT session_id FROM intake_sessions ORDER BY created_at ASC")
            rows = cursor.fetchall()
        
        result = {}
        for r in rows:
            sess = self.get_session(r["session_id"])
            if sess:
                result[sess.session_id] = sess
        return result

    # --------------------------------------------------------------------------
    # CLINICAL SUMMARY
    # --------------------------------------------------------------------------
    def save_clinical_summary(self, session_id: str, sm: StructuredClinicalSummary):
        with self._lock:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO clinical_summaries (
                        summary_id, session_id, patient_id,
                        chief_complaint, duration_of_complaint, history_of_present_illness,
                        past_medical_history, past_surgical_history, drug_allergies,
                        current_medications, family_history, personal_and_social_history,
                        review_of_systems, ayush_assessment, investigation_summary,
                        triage, icd10_suggestions, namaste_suggestions,
                        summary_generated_at, physician_reviewed, physician_notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        chief_complaint=excluded.chief_complaint,
                        duration_of_complaint=excluded.duration_of_complaint,
                        history_of_present_illness=excluded.history_of_present_illness,
                        past_medical_history=excluded.past_medical_history,
                        past_surgical_history=excluded.past_surgical_history,
                        drug_allergies=excluded.drug_allergies,
                        current_medications=excluded.current_medications,
                        family_history=excluded.family_history,
                        personal_and_social_history=excluded.personal_and_social_history,
                        review_of_systems=excluded.review_of_systems,
                        ayush_assessment=excluded.ayush_assessment,
                        investigation_summary=excluded.investigation_summary,
                        triage=excluded.triage,
                        icd10_suggestions=excluded.icd10_suggestions,
                        namaste_suggestions=excluded.namaste_suggestions,
                        physician_reviewed=excluded.physician_reviewed,
                        physician_notes=excluded.physician_notes;
                """, (
                    sm.summary_id, session_id, sm.patient_id,
                    sm.chief_complaint, sm.duration_of_complaint, sm.history_of_present_illness,
                    _json_dumps(sm.past_medical_history),
                    _json_dumps(sm.past_surgical_history),
                    _json_dumps(sm.drug_allergies),
                    _json_dumps(sm.current_medications),
                    _json_dumps(sm.family_history),
                    _json_dumps(sm.personal_and_social_history),
                    _json_dumps(sm.review_of_systems),
                    _json_dumps(sm.ayush_assessment),
                    _json_dumps(sm.investigation_summary),
                    _json_dumps(sm.triage),
                    _json_dumps(sm.icd10_suggestions),
                    _json_dumps(sm.namaste_suggestions),
                    sm.summary_generated_at,
                    1 if sm.physician_reviewed else 0,
                    sm.physician_notes
                ))

    def get_clinical_summary(self, session_id: str) -> Optional[StructuredClinicalSummary]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM clinical_summaries WHERE session_id = ?", (session_id,))
            row = cursor.fetchone()
            if not row:
                return None

        # Reconstruct medications
        meds_raw = _json_loads(row["current_medications"], [])
        current_meds = [ExtractedMedication(**m) if isinstance(m, dict) else m for m in meds_raw]

        # Reconstruct investigations
        inv_raw = _json_loads(row["investigation_summary"], [])
        inv_summary = [ExtractedLabInvestigation(**i) if isinstance(i, dict) else i for i in inv_raw]

        # Reconstruct triage
        triage_raw = _json_loads(row["triage"], {})
        triage = TriageAlert(**triage_raw) if triage_raw else TriageAlert()

        # Reconstruct ayush
        ayush_raw = _json_loads(row["ayush_assessment"])
        ayush = AyushPariksha(**ayush_raw) if ayush_raw else None

        return StructuredClinicalSummary(
            summary_id=row["summary_id"],
            patient_id=row["patient_id"],
            chief_complaint=row["chief_complaint"],
            duration_of_complaint=row["duration_of_complaint"] or "",
            history_of_present_illness=row["history_of_present_illness"] or "",
            past_medical_history=_json_loads(row["past_medical_history"], []),
            past_surgical_history=_json_loads(row["past_surgical_history"], []),
            drug_allergies=_json_loads(row["drug_allergies"], []),
            current_medications=current_meds,
            family_history=_json_loads(row["family_history"], []),
            personal_and_social_history=_json_loads(row["personal_and_social_history"], {}),
            review_of_systems=_json_loads(row["review_of_systems"], {}),
            ayush_assessment=ayush,
            investigation_summary=inv_summary,
            triage=triage,
            icd10_suggestions=_json_loads(row["icd10_suggestions"], []),
            namaste_suggestions=_json_loads(row["namaste_suggestions"], []),
            summary_generated_at=row["summary_generated_at"],
            physician_reviewed=bool(row["physician_reviewed"]),
            physician_notes=row["physician_notes"]
        )

    # --------------------------------------------------------------------------
    # DIGITIZED DOCUMENTS (OCR)
    # --------------------------------------------------------------------------
    def save_document(self, session_id: str, doc: DocumentDigitization):
        with self._lock:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO documents (
                        document_id, session_id, patient_id, document_type,
                        original_filename, upload_timestamp, ocr_raw_text,
                        extracted_diagnoses, extracted_medications, extracted_investigations,
                        historical_date, doctor_or_facility
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(document_id) DO UPDATE SET
                        document_type=excluded.document_type,
                        original_filename=excluded.original_filename,
                        ocr_raw_text=excluded.ocr_raw_text,
                        extracted_diagnoses=excluded.extracted_diagnoses,
                        extracted_medications=excluded.extracted_medications,
                        extracted_investigations=excluded.extracted_investigations,
                        historical_date=excluded.historical_date,
                        doctor_or_facility=excluded.doctor_or_facility;
                """, (
                    doc.document_id, session_id, doc.patient_id, doc.document_type,
                    doc.original_filename, doc.upload_timestamp, doc.ocr_raw_text,
                    _json_dumps(doc.extracted_diagnoses),
                    _json_dumps(doc.extracted_medications),
                    _json_dumps(doc.extracted_investigations),
                    doc.historical_date, doc.doctor_or_facility
                ))

    def get_session_documents(self, session_id: str) -> List[DocumentDigitization]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM documents WHERE session_id = ? ORDER BY upload_timestamp ASC", (session_id,))
            rows = cursor.fetchall()

        docs = []
        for r in rows:
            meds_raw = _json_loads(r["extracted_medications"], [])
            meds = [ExtractedMedication(**m) if isinstance(m, dict) else m for m in meds_raw]

            inv_raw = _json_loads(r["extracted_investigations"], [])
            invs = [ExtractedLabInvestigation(**i) if isinstance(i, dict) else i for i in inv_raw]

            docs.append(DocumentDigitization(
                document_id=r["document_id"],
                patient_id=r["patient_id"],
                document_type=r["document_type"],
                original_filename=r["original_filename"],
                upload_timestamp=r["upload_timestamp"],
                ocr_raw_text=r["ocr_raw_text"] or "",
                extracted_diagnoses=_json_loads(r["extracted_diagnoses"], []),
                extracted_medications=meds,
                extracted_investigations=invs,
                historical_date=r["historical_date"],
                doctor_or_facility=r["doctor_or_facility"]
            ))
        return docs

    # --------------------------------------------------------------------------
    # CONSULTATIONS (DOCTOR DESK & ABDM FHIR)
    # --------------------------------------------------------------------------
    def save_consultation(self, session_id: str, rec: DoctorConsultationRecord):
        with self._lock:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO consultations (
                        consultation_id, session_id, patient_id,
                        doctor_name, doctor_department, diagnosis,
                        icd10_code, ayush_namaste_code, clinical_notes,
                        prescriptions, ordered_investigations, follow_up_date,
                        consultation_timestamp, fhir_bundle_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        doctor_name=excluded.doctor_name,
                        doctor_department=excluded.doctor_department,
                        diagnosis=excluded.diagnosis,
                        icd10_code=excluded.icd10_code,
                        ayush_namaste_code=excluded.ayush_namaste_code,
                        clinical_notes=excluded.clinical_notes,
                        prescriptions=excluded.prescriptions,
                        ordered_investigations=excluded.ordered_investigations,
                        follow_up_date=excluded.follow_up_date,
                        consultation_timestamp=excluded.consultation_timestamp,
                        fhir_bundle_id=excluded.fhir_bundle_id;
                """, (
                    rec.consultation_id, session_id, rec.patient_id,
                    rec.doctor_name, rec.doctor_department, rec.diagnosis,
                    rec.icd10_code, rec.ayush_namaste_code, rec.clinical_notes,
                    _json_dumps(rec.prescriptions),
                    _json_dumps(rec.ordered_investigations),
                    rec.follow_up_date,
                    rec.consultation_timestamp,
                    rec.fhir_bundle_id
                ))
            self.complete_opd_queue_item(session_id)
            self.log_audit("CONSULTATION_COMPLETED", patient_id=rec.patient_id, session_id=session_id)

    def get_consultation(self, session_id: str) -> Optional[DoctorConsultationRecord]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM consultations WHERE session_id = ?", (session_id,))
            r = cursor.fetchone()
            if not r:
                return None

        rx_raw = _json_loads(r["prescriptions"], [])
        prescriptions = [DoctorPrescriptionItem(**p) if isinstance(p, dict) else p for p in rx_raw]

        return DoctorConsultationRecord(
            consultation_id=r["consultation_id"],
            patient_id=r["patient_id"],
            doctor_name=r["doctor_name"],
            doctor_department=r["doctor_department"],
            diagnosis=r["diagnosis"],
            icd10_code=r["icd10_code"],
            ayush_namaste_code=r["ayush_namaste_code"],
            clinical_notes=r["clinical_notes"] or "",
            prescriptions=prescriptions,
            ordered_investigations=_json_loads(r["ordered_investigations"], []),
            follow_up_date=r["follow_up_date"],
            consultation_timestamp=r["consultation_timestamp"],
            fhir_bundle_id=r["fhir_bundle_id"]
        )

    def consultation_exists(self, session_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM consultations WHERE session_id = ?", (session_id,))
            return cursor.fetchone() is not None

    def get_all_consultations(self) -> Dict[str, DoctorConsultationRecord]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT session_id FROM consultations")
            rows = cursor.fetchall()
        result = {}
        for r in rows:
            rec = self.get_consultation(r["session_id"])
            if rec:
                result[r["session_id"]] = rec
        return result

    # --------------------------------------------------------------------------
    # OPD QUEUE
    # --------------------------------------------------------------------------
    def get_opd_queue(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT token, session_id, patient_id, patient_name,
                       age, gender, chief_complaint, stream,
                       triage_level, is_red_flag, waiting_minutes,
                       summary_id, has_scanned_docs, created_at
                FROM opd_queue
                WHERE status = 'waiting'
                ORDER BY id DESC
            """)
            rows = cursor.fetchall()
            return [
                {
                    "token": r["token"],
                    "session_id": r["session_id"],
                    "patient_id": r["patient_id"],
                    "patient_name": r["patient_name"],
                    "age": r["age"],
                    "gender": r["gender"],
                    "chief_complaint": r["chief_complaint"],
                    "stream": r["stream"],
                    "triage_level": r["triage_level"],
                    "is_red_flag": bool(r["is_red_flag"]),
                    "waiting_minutes": r["waiting_minutes"],
                    "summary_id": r["summary_id"],
                    "has_scanned_docs": bool(r["has_scanned_docs"]),
                    "created_at": r["created_at"]
                }
                for r in rows
            ]

    def add_to_opd_queue(self, item: Dict[str, Any]):
        with self._lock:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO opd_queue (
                        token, session_id, patient_id, patient_name,
                        age, gender, chief_complaint, stream,
                        triage_level, is_red_flag, waiting_minutes,
                        summary_id, has_scanned_docs, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'waiting', ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        status='waiting',
                        triage_level=excluded.triage_level,
                        is_red_flag=excluded.is_red_flag,
                        summary_id=excluded.summary_id,
                        has_scanned_docs=excluded.has_scanned_docs;
                """, (
                    item.get("token", ""),
                    item.get("session_id", ""),
                    item.get("patient_id", ""),
                    item.get("patient_name", ""),
                    item.get("age", 0),
                    item.get("gender", "Other"),
                    item.get("chief_complaint", ""),
                    item.get("stream", "allopathy"),
                    item.get("triage_level", "routine"),
                    1 if item.get("is_red_flag") else 0,
                    item.get("waiting_minutes", 0),
                    item.get("summary_id"),
                    1 if item.get("has_scanned_docs") else 0,
                    item.get("created_at", datetime.now().isoformat())
                ))

    def complete_opd_queue_item(self, session_id: str):
        with self._lock:
            with self.get_connection() as conn:
                conn.execute("UPDATE opd_queue SET status = 'completed' WHERE session_id = ?", (session_id,))

    # --------------------------------------------------------------------------
    # EMERGENCY TRIAGE ALERTS
    # --------------------------------------------------------------------------
    def get_triage_alerts(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT token, patient_name, rationale, action, timestamp
                FROM triage_alerts
                WHERE is_resolved = 0
                ORDER BY id DESC
            """)
            rows = cursor.fetchall()
            return [
                {
                    "token": r["token"],
                    "patient_name": r["patient_name"],
                    "rationale": r["rationale"],
                    "action": r["action"],
                    "timestamp": r["timestamp"]
                }
                for r in rows
            ]

    def add_triage_alert(self, alert: Dict[str, Any]):
        with self._lock:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO triage_alerts (
                        token, patient_name, rationale, action, is_resolved, timestamp
                    ) VALUES (?, ?, ?, ?, 0, ?)
                """, (
                    alert.get("token", ""),
                    alert.get("patient_name", ""),
                    alert.get("rationale", ""),
                    alert.get("action", ""),
                    alert.get("timestamp", datetime.now().isoformat())
                ))

    # --------------------------------------------------------------------------
    # AUDIT LOGGING & ANALYTICS
    # --------------------------------------------------------------------------
    def log_audit(self, event_type: str, patient_id: Optional[str] = None,
                  session_id: Optional[str] = None, facility_id: Optional[str] = None,
                  details: Optional[str] = None):
        try:
            with self.get_connection() as conn:
                conn.execute("""
                    INSERT INTO audit_logs (
                        event_type, patient_id, session_id, facility_id, details, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    event_type, patient_id, session_id,
                    facility_id or settings.ABDM_FACILITY_ID,
                    details, datetime.now().isoformat()
                ))
        except Exception:
            pass

    def get_database_stats(self) -> Dict[str, Any]:
        """Provides statistics on database tables, row counts, and disk metrics."""
        tables = [
            "patients", "consents", "intake_sessions", "clinical_summaries",
            "documents", "consultations", "opd_queue", "triage_alerts", "audit_logs"
        ]
        counts = {}
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for t in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) as count FROM {t}")
                    counts[t] = cursor.fetchone()["count"]
                except Exception:
                    counts[t] = 0

            # Get SQLite version and pragmas
            cursor.execute("SELECT sqlite_version() as version")
            sqlite_ver = cursor.fetchone()["version"]

            cursor.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]

        file_size_bytes = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0

        return {
            "status": "healthy",
            "engine": "SQLite Relational Database",
            "sqlite_version": sqlite_ver,
            "journal_mode": journal_mode,
            "database_file": os.path.abspath(self.db_path),
            "file_size_bytes": file_size_bytes,
            "file_size_kb": round(file_size_bytes / 1024, 2),
            "table_counts": counts,
            "timestamp": datetime.now().isoformat()
        }

    # --------------------------------------------------------------------------
    # DEMO DATA SEEDING
    # --------------------------------------------------------------------------
    def seed_initial_demo_data(self):
        """Seeds initial SIH demo patients into the real SQL database."""
        with self._lock:
            # Seed 1: Ramesh Kumar (Allopathy / Cardiology)
            p1 = PatientDemographics(
                patient_id="P-101",
                name="Ramesh Kumar",
                age=58,
                gender="Male",
                phone="9876543210",
                abha_id="ramesh.kumar58@abdm",
                abha_number="91-4829-1029-4412",
                language=LanguageEnum.HI,
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
            self.save_session(sess1)
            self.add_to_opd_queue({
                "token": p1.token_number,
                "session_id": sess1.session_id,
                "patient_id": p1.patient_id,
                "patient_name": p1.name,
                "age": p1.age,
                "gender": p1.gender,
                "chief_complaint": sess1.chief_complaint,
                "stream": p1.stream.value if hasattr(p1.stream, "value") else str(p1.stream),
                "triage_level": tr1.triage_level.value if hasattr(tr1.triage_level, "value") else str(tr1.triage_level),
                "is_red_flag": tr1.is_red_flag,
                "waiting_minutes": 8,
                "summary_id": sum1.summary_id,
                "has_scanned_docs": True,
                "created_at": datetime.now().isoformat()
            })

            # Seed 2: Shanti Devi (AYUSH / Sandhigata Vata)
            p2 = PatientDemographics(
                patient_id="P-102",
                name="Shanti Devi",
                age=52,
                gender="Female",
                phone="9812345678",
                abha_id="shanti.devi52@abdm",
                abha_number="91-5512-8821-9901",
                language=LanguageEnum.HI,
                stream=StreamEnum.AYUSH,
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
            self.save_session(sess2)
            self.add_to_opd_queue({
                "token": p2.token_number,
                "session_id": sess2.session_id,
                "patient_id": p2.patient_id,
                "patient_name": p2.name,
                "age": p2.age,
                "gender": p2.gender,
                "chief_complaint": sess2.chief_complaint,
                "stream": p2.stream.value if hasattr(p2.stream, "value") else str(p2.stream),
                "triage_level": tr2.triage_level.value if hasattr(tr2.triage_level, "value") else str(tr2.triage_level),
                "is_red_flag": tr2.is_red_flag,
                "waiting_minutes": 15,
                "summary_id": sum2.summary_id,
                "has_scanned_docs": True,
                "created_at": datetime.now().isoformat()
            })


# ==============================================================================
# PROXIES FOR BACKWARD COMPATIBILITY
# ==============================================================================

class SessionsProxy:
    """Dictionary-like interface wrapping SQLDatabase sessions with read-through caching."""

    def __init__(self, db: SQLDatabase):
        self._db = db
        self._cache: Dict[str, IntakeSession] = {}

    def __getitem__(self, session_id: str) -> IntakeSession:
        if session_id in self._cache:
            return self._cache[session_id]
        sess = self._db.get_session(session_id)
        if not sess:
            raise KeyError(session_id)
        self._cache[session_id] = sess
        return sess

    def __setitem__(self, session_id: str, session: IntakeSession):
        self._cache[session_id] = session
        self._db.save_session(session)

    def get(self, session_id: str, default: Any = None) -> Optional[IntakeSession]:
        if session_id in self._cache:
            return self._cache[session_id]
        sess = self._db.get_session(session_id)
        if sess is not None:
            self._cache[session_id] = sess
            return sess
        return default

    def __contains__(self, session_id: str) -> bool:
        if session_id in self._cache:
            return True
        return self._db.session_exists(session_id)

    def __len__(self) -> int:
        return self._db.count_sessions()

    def values(self) -> List[IntakeSession]:
        # Sync cache with all database sessions
        db_sessions = self._db.get_all_sessions()
        self._cache.update(db_sessions)
        return list(self._cache.values())

    def items(self) -> List[tuple]:
        self.values()
        return list(self._cache.items())

    def keys(self) -> List[str]:
        self.values()
        return list(self._cache.keys())


class OPDQueueProxy(list):
    """List-like interface wrapping SQLDatabase OPD queue."""

    def __init__(self, db: SQLDatabase):
        super().__init__()
        self._db = db
        self.reload()

    def reload(self):
        super().clear()
        super().extend(self._db.get_opd_queue())

    def insert(self, index: int, item: Dict[str, Any]):
        self._db.add_to_opd_queue(item)
        super().insert(index, item)

    def append(self, item: Dict[str, Any]):
        self._db.add_to_opd_queue(item)
        super().append(item)


class ConsultationsProxy(dict):
    """Dictionary-like interface wrapping SQLDatabase consultations."""

    def __init__(self, db: SQLDatabase):
        super().__init__()
        self._db = db

    def __getitem__(self, session_id: str) -> DoctorConsultationRecord:
        rec = self._db.get_consultation(session_id)
        if not rec:
            raise KeyError(session_id)
        return rec

    def __setitem__(self, session_id: str, record: DoctorConsultationRecord):
        self._db.save_consultation(session_id, record)
        super().__setitem__(session_id, record)

    def get(self, session_id: str, default: Any = None) -> Optional[DoctorConsultationRecord]:
        rec = self._db.get_consultation(session_id)
        return rec if rec is not None else default

    def __contains__(self, session_id: str) -> bool:
        return self._db.consultation_exists(session_id)

    def values(self) -> List[DoctorConsultationRecord]:
        return list(self._db.get_all_consultations().values())

    def items(self) -> List[tuple]:
        return list(self._db.get_all_consultations().items())


class TriageAlertsProxy(list):
    """List-like interface wrapping SQLDatabase emergency triage alerts."""

    def __init__(self, db: SQLDatabase):
        super().__init__()
        self._db = db
        self.reload()

    def reload(self):
        super().clear()
        super().extend(self._db.get_triage_alerts())

    def insert(self, index: int, item: Dict[str, Any]):
        self._db.add_triage_alert(item)
        super().insert(index, item)

    def append(self, item: Dict[str, Any]):
        self._db.add_triage_alert(item)
        super().append(item)
