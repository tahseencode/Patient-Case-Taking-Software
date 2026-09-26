"""
Database Management & Diagnostics API Routes
SIH26047: AI-Powered Digital Clinical Intake Platform
"""

from fastapi import APIRouter
from backend.app.database.db import db
from backend.app.core.config import settings

router = APIRouter(prefix="/database", tags=["Database Management & Diagnostics"])


@router.get("/status")
async def get_database_status():
    """
    Returns real-time health, disk metrics, and relational table row counts
    from the persistent SQLite relational database.
    """
    stats = db.get_database_stats()
    return {
        "success": True,
        "database": stats,
        "facility_id": settings.ABDM_FACILITY_ID,
        "dpdp_version": settings.DPDP_CONSENT_VERSION
    }


@router.get("/tables")
async def list_database_tables():
    """Lists all relational tables and their current record counts."""
    stats = db.get_database_stats()
    return {
        "success": True,
        "tables": stats["table_counts"]
    }
