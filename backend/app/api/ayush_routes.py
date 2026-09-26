from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.core.ayush_engine import ayush_engine
from backend.app.models.schemas import AyushPariksha
from backend.app.database.db import db

router = APIRouter(prefix="/ayush", tags=["AYUSH Ayurvedic Intake"])

class ParikshaCalculationRequest(BaseModel):
    session_id: Optional[str] = None
    answers: Dict[str, str]
    lifestyle_notes: Optional[str] = None
    language: str = "hi"

@router.get("/questions")
async def get_ayush_questions(language: str = "hi"):
    return {
        "success": True,
        "language": language,
        "questions": ayush_engine.get_ayush_questions(language)
    }

@router.post("/calculate-pariksha")
async def calculate_ayush_pariksha(req: ParikshaCalculationRequest):
    pariksha_result: AyushPariksha = ayush_engine.calculate_pariksha(
        answers=req.answers,
        lifestyle_notes=req.lifestyle_notes
    )

    if req.session_id and req.session_id in db.sessions:
        db.sessions[req.session_id].ayush = pariksha_result
        db.save_session(db.sessions[req.session_id])

    return {
        "success": True,
        "pariksha": pariksha_result
    }
