import os
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List

from backend.app.core.config import settings
from backend.app.api.kiosk_routes import router as kiosk_router
from backend.app.api.ayush_routes import router as ayush_router
from backend.app.api.document_routes import router as doc_router
from backend.app.api.doctor_routes import router as doctor_router
from backend.app.api.abdm_routes import router as abdm_router

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="SIH26047: AI-Powered Digital Clinical Intake Platform for Indian OPD & AYUSH Institutions"
)

# Enable CORS for frontend development and kiosk terminals
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(kiosk_router, prefix=settings.API_PREFIX)
app.include_router(ayush_router, prefix=settings.API_PREFIX)
app.include_router(doc_router, prefix=settings.API_PREFIX)
app.include_router(doctor_router, prefix=settings.API_PREFIX)
app.include_router(abdm_router, prefix=settings.API_PREFIX)

# WebSocket Connection Manager for Real-Time OPD Queue and Emergency Triage Alerts
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
        for connection in self.active_connections:
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
            # Echo or broadcast updates
            await manager.broadcast(data)
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/health")
async def api_health():
    return {
        "status": "online",
        "platform": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "facility_id": settings.ABDM_FACILITY_ID,
        "docs_url": "/docs",
        "api_prefix": settings.API_PREFIX
    }

# Mount Frontend static assets
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

