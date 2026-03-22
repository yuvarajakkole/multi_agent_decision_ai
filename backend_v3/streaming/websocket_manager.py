import asyncio
from typing import Dict
from fastapi import WebSocket

class WebSocketManager:
    def __init__(self): self.active:Dict[str,WebSocket]={}; self._lock=asyncio.Lock()
    async def connect(self,rid,ws):
        await ws.accept()
        async with self._lock: self.active[rid]=ws
    async def disconnect(self,rid):
        async with self._lock: self.active.pop(rid,None)
    async def send(self,rid,msg):
        ws=self.active.get(rid)
        if ws:
            try: await ws.send_json(msg)
            except: pass

ws_manager=WebSocketManager()
