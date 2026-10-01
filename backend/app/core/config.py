import os
import shutil
from pydantic import BaseModel


def _resolve_db_path() -> str:
    """Return a writable SQLite path.

    Locally the bundled DB file is used directly. On Vercel the deployment
    filesystem is read-only (only /tmp is writable), so the bundled DB is
    copied to /tmp on cold start and used from there. Data written there is
    ephemeral - use a hosted database for real persistence.
    """
    bundled = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "database", "patient_intake.db")
    )
    explicit = os.getenv("DATABASE_PATH")
    if explicit:
        return explicit
    if os.getenv("VERCEL"):
        tmp_path = "/tmp/patient_intake.db"
        if not os.path.exists(tmp_path) and os.path.exists(bundled):
            shutil.copyfile(bundled, tmp_path)
        return tmp_path
    return bundled


_DB_PATH = _resolve_db_path()

class Settings(BaseModel):
    APP_NAME: str = "MediKiosk - AI Clinical Intake Platform"
    APP_VERSION: str = "2.0.0-SIH26047"
    API_PREFIX: str = "/api/v1"
    ABDM_FACILITY_ID: str = "IN-AIIMS-DELHI-0012"
    ABDM_HIE_CM_URL: str = "https://hie-cm.abdm.gov.in"
    DPDP_CONSENT_VERSION: str = "DPDP-ACT-2023-V1.4"
    DEFAULT_LANGUAGE: str = "hi"
    EMERGENCY_DESK_ID: str = "TRIAGE-DESK-OPD-01"
    
    # Database configuration (defaults to persistent SQLite database)
    DATABASE_PATH: str = _DB_PATH
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{_DB_PATH}")

    # LLM Settings (optional keys - offline rule/NLP engine works 100% reliably out of the box)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

settings = Settings()
