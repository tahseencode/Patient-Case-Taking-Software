import os
import sys
from datetime import datetime, timezone

# Ensure project root is in sys.path so 'backend' is importable regardless of invocation directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from fastapi import Depends, FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.app.core.config import settings
from backend.app.core.security import require_staff, verify_key
from backend.app.core.realtime import manager
from backend.app.api.kiosk_routes import router as kiosk_router
from backend.app.api.doctor_routes import router as doctor_router
from backend.app.api.document_routes import router as document_router
from backend.app.api.ayush_routes import router as ayush_router
from backend.app.api.abdm_routes import router as abdm_router
from backend.app.api.database_routes import router as database_router


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Digital Clinical Intake Platform for OPD queues",
)


# ── CORS ──────────────────────────────────────────────────────────────
# The frontend is served from the same origin, so no cross-origin access is
# needed by default. Set ALLOWED_ORIGINS="https://a.com,https://b.com" to add some.
_ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)


# ── Security headers ──────────────────────────────────────────────────
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    response.headers.setdefault("Permissions-Policy", "camera=(), geolocation=()")
    if request.url.path.startswith(("/api", "/v1", "/ws")):
        response.headers["Cache-Control"] = "no-store"  # never cache patient data
    return response


# ── Never leak stack traces to clients ────────────────────────────────
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    import logging
    logging.getLogger("medikiosk").exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# ── Register API routers under /api/v1 and /v1 (dual mounting for serverless proxy safety) ──
_staff = [Depends(require_staff)]
for prefix in [settings.API_PREFIX, "/v1"]:
    app.include_router(kiosk_router, prefix=prefix)
    app.include_router(doctor_router, prefix=prefix, dependencies=_staff)     # PII + clinical data
    app.include_router(document_router, prefix=prefix)                         # per-route auth inside
    app.include_router(ayush_router, prefix=prefix)
    app.include_router(abdm_router, prefix=prefix)                             # per-route auth inside
    app.include_router(database_router, prefix=prefix, dependencies=_staff)   # diagnostics


# ── Health endpoints ──────────────────────────────────────────────────
@app.get("/api/health")
@app.get("/health")
@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "online",
        "platform": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "facility_id": settings.ABDM_FACILITY_ID,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ── Frontend static files mounting & routes ───────────────────────────
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FRONTEND_DIR = os.path.join(_BASE_DIR, "frontend")

_IS_SERVERLESS = bool(os.getenv("VERCEL") or os.getenv("VERCEL_ENV") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))

if os.path.exists(_FRONTEND_DIR) and not _IS_SERVERLESS:
    css_dir = os.path.join(_FRONTEND_DIR, "css")
    js_dir = os.path.join(_FRONTEND_DIR, "js")
    assets_dir = os.path.join(_FRONTEND_DIR, "assets")

    if os.path.exists(css_dir):
        try:
            app.mount("/css", StaticFiles(directory=css_dir), name="css")
        except Exception:
            pass
    if os.path.exists(js_dir):
        try:
            app.mount("/js", StaticFiles(directory=js_dir), name="js")
        except Exception:
            pass
    if os.path.exists(assets_dir):
        try:
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")
        except Exception:
            pass

    @app.get("/", include_in_schema=False)
    async def serve_root():
        index_file = os.path.join(_FRONTEND_DIR, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return JSONResponse({
            "message": f"{settings.APP_NAME} v{settings.APP_VERSION}",
            "docs": "/docs",
            "health": "/api/health",
        })

    @app.get("/index.html", include_in_schema=False)
    async def serve_index():
        return FileResponse(os.path.join(_FRONTEND_DIR, "index.html"))

    @app.get("/app.html", include_in_schema=False)
    @app.get("/app", include_in_schema=False)
    async def serve_app():
        return FileResponse(os.path.join(_FRONTEND_DIR, "app.html"))

    @app.get("/style.css", include_in_schema=False)
    async def serve_style():
        return FileResponse(os.path.join(_FRONTEND_DIR, "style.css"))
else:
    @app.get("/")
    async def root():
        return {
            "message": f"{settings.APP_NAME} v{settings.APP_VERSION}",
            "docs": "/docs",
            "health": "/api/health",
        }


# ── Live feed (staff-only, server-broadcast, clients are listen-only) ──
_WS_MAX_MESSAGE_BYTES = 4096


@app.websocket("/ws/live-feed")
async def websocket_endpoint(websocket: WebSocket):
    # Browsers cannot set headers on WebSockets, so the key comes via query param.
    # Origin must match Host (blocks cross-site WebSocket hijacking).
    origin = websocket.headers.get("origin")
    host = websocket.headers.get("host")
    if origin and host and origin.split("://", 1)[-1] != host and origin not in _ALLOWED_ORIGINS:
        await websocket.close(code=1008)
        return
    if not verify_key(websocket.query_params.get("key")):
        await websocket.close(code=1008)
        return
    await manager.connect(websocket)
    try:
        while True:
            msg = await websocket.receive_text()  # read only to detect disconnects; never rebroadcast
            if len(msg) > _WS_MAX_MESSAGE_BYTES:
                await websocket.close(code=1009)
                break
    except WebSocketDisconnect:
        pass
    except Exception:
        pass
    finally:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)