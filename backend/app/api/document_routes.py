from typing import Dict, Any, List, Optional
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from backend.app.core.ocr_engine import ocr_engine
from backend.app.sample_data.sample_documents import SAMPLE_DOCUMENTS
from backend.app.database.db import db
from backend.app.models.schemas import DocumentDigitization

router = APIRouter(prefix="/documents", tags=["Medical Document Digitization & OCR"])

class LoadSampleRequest(BaseModel):
    session_id: str
    sample_id: str

class TextOCRRequest(BaseModel):
    session_id: str
    filename: str
    raw_text: str
    doc_type: Optional[str] = "prescription"

@router.get("/sample-library")
async def get_sample_document_library():
    return {
        "success": True,
        "samples": SAMPLE_DOCUMENTS
    }

@router.post("/load-sample")
async def load_sample_document(req: LoadSampleRequest):
    session = db.sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Intake session not found")

    sample = next((s for s in SAMPLE_DOCUMENTS if s["id"] == req.sample_id), None)
    if not sample:
        raise HTTPException(status_code=404, detail="Sample document not found")

    digitized = ocr_engine.process_document(
        filename=f"{sample['id']}.pdf",
        text_content=sample["preview_text"],
        patient_id=session.patient.patient_id,
        doc_type=sample["doc_type"]
    )

    session.documents.append(digitized)

    return {
        "success": True,
        "document": digitized,
        "total_documents": len(session.documents)
    }

@router.post("/upload-ocr")
async def upload_and_process_document(
    session_id: str = Form(...),
    doc_type: str = Form("prescription"),
    filename: Optional[str] = Form("scanned_prescription.txt"),
    raw_text: Optional[str] = Form(None)
):
    session = db.sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Intake session not found")

    text_to_process = raw_text or "Rx: Tab Telma-H 40mg 1-0-0, Tab Glycomet 500mg 1-0-1. Diagnosis: Hypertension, T2DM."
    
    digitized = ocr_engine.process_document(
        filename=filename or "scanned_doc.pdf",
        text_content=text_to_process,
        patient_id=session.patient.patient_id,
        doc_type=doc_type
    )

    session.documents.append(digitized)

    return {
        "success": True,
        "document": digitized,
        "total_documents": len(session.documents)
    }

@router.get("/session-documents/{session_id}")
async def get_session_documents(session_id: str):
    session = db.sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Intake session not found")

    return {
        "success": True,
        "documents": session.documents
    }
