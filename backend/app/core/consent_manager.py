import hashlib
import json
from datetime import datetime
from backend.app.models.schemas import DPDP2023Consent

class ConsentManager:
    @staticmethod
    def create_consent_artifact(
        patient_id: str,
        voice_allowed: bool = True,
        ocr_allowed: bool = True,
        abha_allowed: bool = True,
        research_allowed: bool = False,
        audio_verified: bool = True
    ) -> DPDP2023Consent:
        ts = datetime.now().isoformat()
        raw_data = {
            "patient_id": patient_id,
            "timestamp": ts,
            "voice_capture_allowed": voice_allowed,
            "ocr_processing_allowed": ocr_allowed,
            "abha_data_sharing_allowed": abha_allowed,
            "anonymized_research_allowed": research_allowed,
            "framework": "Digital Personal Data Protection Act 2023 (DPDPA-India)",
            "purpose": "Clinical triage, OPD pre-consultation history intake, and ABDM interoperability."
        }
        
        # Cryptographic SHA-256 audit fingerprint
        canonical_str = json.dumps(raw_data, sort_keys=True)
        consent_hash = hashlib.sha256(canonical_str.encode('utf-8')).hexdigest()

        return DPDP2023Consent(
            consent_id=f"DPDP-{consent_hash[:12].upper()}",
            patient_id=patient_id,
            timestamp=ts,
            voice_capture_allowed=voice_allowed,
            ocr_processing_allowed=ocr_allowed,
            abha_data_sharing_allowed=abha_allowed,
            anonymized_research_allowed=research_allowed,
            consent_version="DPDP-2023-V1.4",
            audio_consent_verified=audio_verified,
            consent_hash=consent_hash
        )

consent_manager = ConsentManager()
