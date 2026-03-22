import asyncio
from typing import Dict
from fastapi import WebSocket


class WebSocketManager:
    def __init__(self):
        self.active: Dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()

    async def connect(self, request_id: str, websocket: WebSocket):
        await websocket.accept()
        async with self._lock:
            self.active[request_id] = websocket

    async def disconnect(self, request_id: str):
        async with self._lock:
            self.active.pop(request_id, None)

    async def send(self, request_id: str, message: dict):
        ws = self.active.get(request_id)
        if ws:
            try:
                await ws.send_json(message)
            except Exception:
                pass

    async def broadcast(self, message: dict):
        async with self._lock:
            for ws in self.active.values():
                try:
                    await ws.send_json(message)
                except Exception:
                    pass


ws_manager = WebSocketManager()
