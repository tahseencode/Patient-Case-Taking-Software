import os
import shutil
from pydantic import BaseModel


def _resolve_db_path() -> str:
    """Return a writable SQLite path.

    Locally the bundled DB file is used directly if writable. On Vercel / serverless
    environments where the deployment root is read-only (only /tmp is writable),
    the bundled DB is copied to /tmp on cold start (or fresh DB initialized there).
    """
    explicit = os.getenv("DATABASE_PATH")
    if explicit:
        return explicit

    bundled = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "database", "patient_intake.db")
    )

    is_serverless = (
        bool(os.getenv("VERCEL"))
        or bool(os.getenv("VERCEL_ENV"))
        or bool(os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
        or bool(os.getenv("LAMBDA_TASK_ROOT"))
        or not os.access(os.path.dirname(bundled) if os.path.exists(os.path.dirname(bundled)) else ".", os.W_OK)
    )

    if is_serverless:
        tmp_path = "/tmp/patient_intake.db"
        if not os.path.exists(tmp_path) and os.path.exists(bundled):
            try:
                shutil.copyfile(bundled, tmp_path)
            except Exception:
                pass
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
