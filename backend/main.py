"""
MediKiosk & AyurKiosk - FastAPI Application
SIH26047: AI-Powered Digital Clinical Intake Platform

Creates the FastAPI application instance and registers all API routers.
"""

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


# ── Health / root endpoints ───────────────────────────────────────────
@app.get("/api/health")
async def health_check():
    return {
        "status": "online",
        "platform": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "facility_id": settings.ABDM_FACILITY_ID,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/")
async def root():
    return {
        "message": f"{settings.APP_NAME} v{settings.APP_VERSION}",
        "docs": "/docs",
        "health": "/api/health",
    }
