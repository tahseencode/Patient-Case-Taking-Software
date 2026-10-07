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
    app = FastAPI(title="MediKiosk - startup error")

    @app.get("/{path:path}")
    @app.post("/{path:path}")
    async def _error_handler(path: str = ""):
        return JSONResponse(
            status_code=500,
            content={"error": "App failed to start", "detail": _tb},
        )
