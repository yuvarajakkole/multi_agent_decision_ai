import asyncio
from typing import Dict
from fastapi import WebSocket


class WebSocketManager:
    """
    Manages active WebSocket connections keyed by request_id.
    Thread-safe via asyncio.Lock for concurrent async access.
    """

    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.lock = asyncio.Lock()

    async def connect(self, request_id: str, websocket: WebSocket):
        """Register a new WebSocket connection. Note: websocket.accept()
        must be called by the route handler BEFORE calling connect()."""
        async with self.lock:
            self.active_connections[request_id] = websocket
        print(f"WebSocket connected: {request_id}")

    async def disconnect(self, request_id: str):
        """Remove a WebSocket connection on client disconnect."""
        async with self.lock:
            if request_id in self.active_connections:
                del self.active_connections[request_id]
        print(f"WebSocket disconnected: {request_id}")

    async def send(self, request_id: str, message: dict):
        """Send a JSON message to a specific connection. Silently skips
        if the connection no longer exists (client already disconnected)."""
        websocket = self.active_connections.get(request_id)
        if websocket:
            try:
                await websocket.send_json(message)
            except Exception as e:
                print(f"WebSocket send error [{request_id}]: {e}")
                await self.disconnect(request_id)

    async def broadcast(self, message: dict):
        """Send a message to all active connections."""
        async with self.lock:
            connections = list(self.active_connections.items())
        for request_id, websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception:
                await self.disconnect(request_id)


# Global singleton — shared across all routes and agents
ws_manager = WebSocketManager()
