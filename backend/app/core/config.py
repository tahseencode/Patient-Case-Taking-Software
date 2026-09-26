import os
from pydantic import BaseModel

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
    DATABASE_PATH: str = os.getenv(
        "DATABASE_PATH",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "patient_intake.db"))
    )
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database', 'patient_intake.db'))}")

    # LLM Settings (optional keys - offline rule/NLP engine works 100% reliably out of the box)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

settings = Settings()
