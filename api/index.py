"""Vercel Serverless Function entrypoint.

This module exposes the FastAPI ASGI `app` instance so Vercel can automatically
discover and execute it within the serverless Python runtime.
"""
import os
import sys
import traceback

# Ensure project root is in sys.path so 'backend' package is importable
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")

for _p in (ROOT_DIR, BACKEND_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from backend.main import app  # noqa: E402, F401
except Exception as _import_err:
    # Fallback: surface the real error as a JSON response instead of a
    # cryptic Vercel "FUNCTION_INVOCATION_FAILED" page.
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    _tb = traceback.format_exc()
    print(_tb, file=sys.stderr)  # always visible in Vercel function logs
    # Surface startup exception details for fast diagnosis on Vercel
    app = FastAPI(title="MediKiosk - startup error", docs_url=None, redoc_url=None, openapi_url=None)

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
    async def _error_handler(path: str = ""):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Backend application failed to initialize on Vercel",
                "exception": str(_import_err),
                "traceback": _tb.splitlines()[-6:] if _tb else [],
            }
        )
