"""Server-side live feed. Only the server broadcasts; clients are listen-only."""
from typing import List
from fastapi import WebSocket


MAX_CONNECTIONS = 50  # Prevent memory-exhaustion DoS


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> bool:
        """Accept and track a WebSocket. Returns False if the limit is reached."""
        if len(self.active_connections) >= MAX_CONNECTIONS:
            await websocket.close(code=1013)  # 1013 = Try Again Later
            return False
        await websocket.accept()
        self.active_connections.append(websocket)
        return True

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)


manager = ConnectionManager()

