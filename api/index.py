"""Vercel Serverless Function entrypoint (api/index.py).

Uses a plain, static import so Vercel's bundler can trace it, and falls back to a
tiny error app (instead of a cryptic FUNCTION_INVOCATION_FAILED page) if the real
app cannot be imported. The full traceback always goes to Vercel Logs.
To also see it in the browser, temporarily set env var DEBUG_STARTUP_ERRORS=1.
"""
import os
import sys
import traceback

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from backend.main import app  # noqa: E402,F401
except Exception:  # pragma: no cover
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse

    _tb = traceback.format_exc()
    print(_tb, file=sys.stderr)
    _expose = os.getenv("DEBUG_STARTUP_ERRORS") == "1"

    app = FastAPI(title="Startup error", docs_url=None, redoc_url=None, openapi_url=None)

    @app.get("/{path:path}")
    @app.post("/{path:path}")
    async def _startup_error(path: str = ""):
        body = {"error": "App failed to start"}
        if _expose:
            body["detail"] = _tb
        return JSONResponse(status_code=500, content=body)