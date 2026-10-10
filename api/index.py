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
    # Fallback: return a clean JSON error instead of a cryptic Vercel
    # "FUNCTION_INVOCATION_FAILED" page. The full traceback always goes to the
    # Vercel function logs, and is only shown in the HTTP response if you opt in
    # by setting DEBUG_STARTUP_ERRORS=1 (use temporarily, then remove it).
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    _tb = traceback.format_exc()
    print(_tb, file=sys.stderr)
    _expose = os.getenv("DEBUG_STARTUP_ERRORS") == "1"
    app = FastAPI(
        title="MediKiosk - startup error",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )

    @app.get("/{path:path}")
    @app.post("/{path:path}")
    async def _error_handler(path: str = ""):
        content = {"error": "App failed to start"}
        if _expose:
            content["detail"] = _tb
        return JSONResponse(status_code=500, content=content)