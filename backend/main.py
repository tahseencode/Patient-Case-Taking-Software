import os
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from backend.app.core.config import settings
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


# CORS - allow all origins for development / Vercel preview deployments
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register API routers under /api/v1 ────────────────────────────────
app.include_router(kiosk_router, prefix=settings.API_PREFIX)
app.include_router(doctor_router, prefix=settings.API_PREFIX)
app.include_router(document_router, prefix=settings.API_PREFIX)
app.include_router(ayush_router, prefix=settings.API_PREFIX)
app.include_router(abdm_router, prefix=settings.API_PREFIX)
app.include_router(database_router, prefix=settings.API_PREFIX)


# ── Health endpoints ──────────────────────────────────────────────────
@app.get("/api/health")
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

if os.path.exists(_FRONTEND_DIR):
    css_dir = os.path.join(_FRONTEND_DIR, "css")
    js_dir = os.path.join(_FRONTEND_DIR, "js")
    assets_dir = os.path.join(_FRONTEND_DIR, "assets")

    if os.path.exists(css_dir):
        app.mount("/css", StaticFiles(directory=css_dir), name="css")
    if os.path.exists(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="js")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

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

