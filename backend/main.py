import os
import sys
from datetime import datetime, timezone
from typing import List

# Ensure project root is in sys.path so 'backend' is importable regardless of invocation directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
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

# ── Register API routers under /api/v1 and /v1 (dual mounting for serverless proxy safety) ──
for prefix in [settings.API_PREFIX, "/v1"]:
    app.include_router(kiosk_router, prefix=prefix)
    app.include_router(doctor_router, prefix=prefix)
    app.include_router(document_router, prefix=prefix)
    app.include_router(ayush_router, prefix=prefix)
    app.include_router(abdm_router, prefix=prefix)
    app.include_router(database_router, prefix=prefix)


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


# ── WebSocket Connection Manager for Real-Time OPD Queue & Emergency Triage ──
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

@app.websocket("/ws/live-feed")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

