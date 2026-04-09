import json
from typing import Dict, List

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, game_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(game_id, []).append(websocket)

    def disconnect(self, game_id: int, websocket: WebSocket):
        sockets = self.active_connections.get(game_id, [])
        if websocket in sockets:
            sockets.remove(websocket)

    async def broadcast(self, game_id: int, message: dict):
        payload = json.dumps(message)
        for connection in list(self.active_connections.get(game_id, [])):
            try:
                await connection.send_text(payload)
            except Exception:
                self.disconnect(game_id, connection)


manager = ConnectionManager()
