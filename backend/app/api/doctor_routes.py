import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.models.schemas import (
    DoctorConsultationRecord, DoctorPrescriptionItem,
    StructuredClinicalSummary
)
from backend.app.core.fhir_builder import abdm_fhir_builder
from backend.app.database.db import db

router = APIRouter(prefix="/doctor", tags=["Physician OPD Consultation Desk"])

class UpdateSummaryRequest(BaseModel):
    session_id: str
    chief_complaint: Optional[str] = None
    history_of_present_illness: Optional[str] = None
    physician_notes: Optional[str] = None
    past_medical_history: Optional[List[str]] = None

class CompleteConsultationRequest(BaseModel):
    session_id: str
    doctor_name: str = "Dr. S. K. Mukherjee, MD"
    doctor_department: str = "General Medicine / OPD"
    diagnosis: str
    icd10_code: Optional[str] = None
    ayush_namaste_code: Optional[str] = None
    clinical_notes: str
    prescriptions: List[DoctorPrescriptionItem] = []
    ordered_investigations: List[str] = []
    follow_up_date: Optional[str] = "After 2 weeks"

@router.get("/opd-queue")
async def get_opd_queue():
    return {
        "success": True,
        "total_waiting": len(db.opd_queue),
        "queue": db.opd_queue
    }

@router.get("/triage-alerts")
async def get_triage_alerts():
    return {
        "success": True,
        "active_emergency_alerts": db.triage_alerts
    }

@router.get("/patient-summary/{session_id}")
async def get_patient_summary(session_id: str):
    session = db.sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Intake session not found")

    return {
        "success": True,
        "session_id": session_id,
        "patient": session.patient,
        "consent": session.consent,
        "summary": session.summary,
        "socrates": session.socrates,
        "ayush": session.ayush,
        "documents": session.documents,
        "triage": session.triage,
        "is_completed": session.is_completed
    }

@router.post("/update-summary")
async def update_patient_summary(req: UpdateSummaryRequest):
    session = db.sessions.get(req.session_id)
    if not session or not session.summary:
        raise HTTPException(status_code=404, detail="Summary not found for this session")

    if req.chief_complaint:
        session.summary.chief_complaint = req.chief_complaint
    if req.history_of_present_illness:
        session.summary.history_of_present_illness = req.history_of_present_illness
    if req.physician_notes:
        session.summary.physician_notes = req.physician_notes
    if req.past_medical_history is not None:
        session.summary.past_medical_history = req.past_medical_history

    session.summary.physician_reviewed = True

    return {
        "success": True,
        "summary": session.summary
    }

@router.post("/prescribe-and-complete")
async def complete_consultation(req: CompleteConsultationRequest):
    session = db.sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Intake session not found")

    consultation_id = f"CONS-{uuid.uuid4().hex[:8].upper()}"

    # Generate ABDM FHIR R4 Bundle
    fhir_bundle = None
    if session.summary:
        session.summary.physician_reviewed = True
        session.summary.physician_notes = req.clinical_notes

    record = DoctorConsultationRecord(
        consultation_id=consultation_id,
        patient_id=session.patient.patient_id,
        doctor_name=req.doctor_name,
        doctor_department=req.doctor_department,
        diagnosis=req.diagnosis,
        icd10_code=req.icd10_code,
        ayush_namaste_code=req.ayush_namaste_code,
        clinical_notes=req.clinical_notes,
        prescriptions=req.prescriptions,
        ordered_investigations=req.ordered_investigations,
        follow_up_date=req.follow_up_date,
        consultation_timestamp=datetime.now().isoformat()
    )

    if session.summary:
        fhir_bundle = abdm_fhir_builder.build_fhir_bundle(
            patient=session.patient,
            summary=session.summary,
            consultation=record
        )
        record.fhir_bundle_id = fhir_bundle.get("id")

    db.consultations[req.session_id] = record

    # Remove from active queue or mark completed
    db.opd_queue = [q for q in db.opd_queue if q.get("session_id") != req.session_id]

    return {
        "success": True,
        "consultation": record,
        "fhir_bundle": fhir_bundle,
        "message": "Consultation successfully completed and pushed to ABDM Health Record."
    }
