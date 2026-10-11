"""Authentication helpers for staff-only endpoints.

Doctor / admin / FHIR endpoints expose patient PII and clinical data, so they
require an API key sent in the `X-API-Key` header. Set `STAFF_API_KEY` in your
environment (Vercel: Project -> Settings -> Environment Variables).

If the key is not configured the endpoints are DENIED, unless APP_ENV=development
is set (local dev only).
"""
import hmac
import os

from fastapi import Header, HTTPException, status


def _is_dev() -> bool:
    return os.getenv("APP_ENV", "production").lower() == "development"


def verify_key(candidate: str | None) -> bool:
    expected = os.getenv("STAFF_API_KEY", "")
    if not expected:
        return _is_dev()
    if not candidate:
        return False
    return hmac.compare_digest(candidate.encode(), expected.encode())


async def require_staff(x_api_key: str | None = Header(default=None)) -> None:
    if not verify_key(x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Staff authentication required",
            headers={"WWW-Authenticate": "ApiKey"},
        )
