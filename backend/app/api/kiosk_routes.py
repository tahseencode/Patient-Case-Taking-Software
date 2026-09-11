import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from backend.app.models.schemas import (
    PatientDemographics, DPDP2023Consent, SocratesResponse,
    IntakeSession, TriageLevel, LanguageEnum
)
from backend.app.core.dialogue_engine import dialogue_engine
from backend.app.core.triage_detector import triage_detector
from backend.app.core.summarizer import clinical_summarizer
from backend.app.core.consent_manager import consent_manager
from backend.app.database.db import db

router = APIRouter(prefix="/kiosk", tags=["Kiosk Intake Engine"])

class StartSessionRequest(BaseModel):
    name: str
    age: int
    gender: str
    phone: str
    abha_id: Optional[str] = None
    language: LanguageEnum = LanguageEnum.HI
    stream: str = "allopathy"
    voice_consent: bool = True
    ocr_consent: bool = True
    abha_consent: bool = True

class VoiceParseRequest(BaseModel):
    transcript: str
    chief_complaint_id: Optional[str] = None
    language: str = "hi"

class SubmitSocratesRequest(BaseModel):
    session_id: str
    chief_complaint_id: str
    chief_complaint_title: str
    affected_body_part: Optional[str] = None
    socrates: SocratesResponse

class FinalizeIntakeRequest(BaseModel):
    session_id: str

@router.get("/complaints")
async def get_chief_complaints(language: str = "hi"):
    return {
        "success": True,
        "language": language,
        "complaints": dialogue_engine.get_chief_complaints(language)
    }

@router.get("/socrates-step")
async def get_socrates_step(step: int = 0, language: str = "hi"):
    step_data = dialogue_engine.get_socrates_question(step, language)
    if not step_data:
        return {"success": False, "message": "No more steps in SOCRATES framework", "is_complete": True}
    return {
        "success": True,
        "data": step_data
    }

@router.post("/parse-voice")
async def parse_voice_transcript(req: VoiceParseRequest):
    extracted = dialogue_engine.parse_voice_transcript(req.transcript, req.chief_complaint_id)
    return {
        "success": True,
        "extracted": extracted
    }

@router.post("/start-session")
async def start_kiosk_session(req: StartSessionRequest):
    sess_id = f"SESS-{uuid.uuid4().hex[:8].upper()}"
    pat_id = f"P-{uuid.uuid4().hex[:6].upper()}"

    consent = consent_manager.create_consent_artifact(
        patient_id=pat_id,
        voice_allowed=req.voice_consent,
        ocr_allowed=req.ocr_consent,
        abha_allowed=req.abha_consent
    )

    token_prefix = "AYU" if req.stream == "ayush" else "OPD"
    token_num = f"{token_prefix}-{len(db.opd_queue) + 1:02d}"

    patient = PatientDemographics(
        patient_id=pat_id,
        name=req.name,
        age=req.age,
        gender=req.gender,
        phone=req.phone,
        abha_id=req.abha_id,
        language=req.language,
        stream=req.stream,
        token_number=token_num
    )

    session = IntakeSession(
        session_id=sess_id,
        patient=patient,
        consent=consent
    )

    db.sessions[sess_id] = session

    return {
        "success": True,
        "session_id": sess_id,
        "patient": patient,
        "consent": consent,
        "token_number": token_num
    }

@router.post("/submit-socrates")
async def submit_socrates_data(req: SubmitSocratesRequest):
    session = db.sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Intake session not found")

    session.chief_complaint = req.chief_complaint_title
    session.affected_body_part = req.affected_body_part
    session.socrates = req.socrates

    # Evaluate real-time triage red flags
    triage_result = triage_detector.evaluate_triage(
        chief_complaint_id=req.chief_complaint_id,
        socrates=req.socrates,
        age=session.patient.age
    )
    session.triage = triage_result

    return {
        "success": True,
        "session_id": req.session_id,
        "triage": triage_result
    }

@router.post("/finalize-intake")
async def finalize_intake_session(req: FinalizeIntakeRequest):
    session = db.sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Intake session not found")

    # Generate Clinical Summary
    summary = clinical_summarizer.generate_summary(
        patient=session.patient,
        chief_complaint_id=session.affected_body_part or "general",
        chief_complaint_title=session.chief_complaint or "General OPD Consultation",
        socrates=session.socrates,
        documents=session.documents,
        triage=session.triage,
        ayush=session.ayush
    )
    session.summary = summary
    session.is_completed = True

    # Add to OPD Queue
    queue_item = {
        "token": session.patient.token_number,
        "session_id": session.session_id,
        "patient_id": session.patient.patient_id,
        "patient_name": session.patient.name,
        "age": session.patient.age,
        "gender": session.patient.gender,
        "chief_complaint": session.chief_complaint,
        "stream": session.patient.stream,
        "triage_level": session.triage.triage_level,
        "is_red_flag": session.triage.is_red_flag,
        "waiting_minutes": 2,
        "summary_id": summary.summary_id,
        "has_scanned_docs": len(session.documents) > 0,
        "created_at": datetime.now().isoformat()
    }
    db.opd_queue.insert(0, queue_item)

    if session.triage.is_red_flag:
        db.triage_alerts.insert(0, {
            "token": session.patient.token_number,
            "patient_name": session.patient.name,
            "rationale": session.triage.clinical_rationale,
            "action": session.triage.recommended_action,
            "timestamp": datetime.now().isoformat()
        })

    return {
        "success": True,
        "token_number": session.patient.token_number,
        "summary": summary,
        "triage": session.triage,
        "message": "Clinical intake successfully registered and routed to OPD physician."
    }
