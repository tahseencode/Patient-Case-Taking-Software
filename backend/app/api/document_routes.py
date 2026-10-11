import os
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field

from backend.app.core.security import require_staff

from backend.app.core.ocr_engine import ocr_engine
from backend.app.sample_data.sample_documents import SAMPLE_DOCUMENTS
from backend.app.database.db import db
from backend.app.models.schemas import DocumentDigitization

router = APIRouter(prefix="/documents", tags=["Medical Document Digitization & OCR"])

class LoadSampleRequest(BaseModel):
    session_id: str = Field(max_length=64)
    sample_id: str = Field(max_length=64)

class TextOCRRequest(BaseModel):
    session_id: str = Field(max_length=64)
    filename: str = Field(max_length=200)
    raw_text: str = Field(max_length=20000)
    doc_type: Optional[str] = Field("prescription", max_length=50)

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
    db.save_document(session.session_id, digitized)

    return {
        "success": True,
        "document": digitized,
        "total_documents": len(session.documents)
    }

@router.post("/upload-ocr")
async def upload_and_process_document(
    session_id: str = Form(..., max_length=64),
    doc_type: str = Form("prescription", max_length=50),
    filename: Optional[str] = Form("scanned_prescription.txt", max_length=200),
    raw_text: Optional[str] = Form(None, max_length=20000)
):
    session = db.sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Intake session not found")

    filename = os.path.basename((filename or "scanned_doc.pdf").replace("\\", "/"))
    text_to_process = raw_text or "Rx: Tab Telma-H 40mg 1-0-0, Tab Glycomet 500mg 1-0-1. Diagnosis: Hypertension, T2DM."
    
    digitized = ocr_engine.process_document(
        filename=filename or "scanned_doc.pdf",
        text_content=text_to_process,
        patient_id=session.patient.patient_id,
        doc_type=doc_type
    )

    session.documents.append(digitized)
    db.save_document(session.session_id, digitized)

    return {
        "success": True,
        "document": digitized,
        "total_documents": len(session.documents)
    }

@router.get("/session-documents/{session_id}", dependencies=[Depends(require_staff)])
async def get_session_documents(session_id: str):
    session = db.sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Intake session not found")

    return {
        "success": True,
        "documents": session.documents
    }
