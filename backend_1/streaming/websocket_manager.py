import asyncio
from typing import Dict
from fastapi import WebSocket


# ---------------------------------------------------------
# CONNECTION MANAGER
# ---------------------------------------------------------

class WebSocketManager:

    def __init__(self):

        self.active_connections: Dict[str, WebSocket] = {}

        self.lock = asyncio.Lock()


    # -----------------------------------------------------
    # CONNECT
    # -----------------------------------------------------

    async def connect(self, request_id: str, websocket: WebSocket):

        await websocket.accept()

        async with self.lock:

            self.active_connections[request_id] = websocket


    # -----------------------------------------------------
    # DISCONNECT
    # -----------------------------------------------------

    async def disconnect(self, request_id: str):

        async with self.lock:

            if request_id in self.active_connections:

                del self.active_connections[request_id]


    # -----------------------------------------------------
    # SEND MESSAGE
    # -----------------------------------------------------

    async def send(self, request_id: str, message: dict):

        websocket = self.active_connections.get(request_id)

        if websocket:

            await websocket.send_json(message)


    # -----------------------------------------------------
    # BROADCAST
    # -----------------------------------------------------

    async def broadcast(self, message: dict):

        async with self.lock:

            for websocket in self.active_connections.values():

                await websocket.send_json(message)


# ---------------------------------------------------------
# GLOBAL INSTANCE
# ---------------------------------------------------------

ws_manager = WebSocketManager()





# from typing import Dict
# from fastapi import WebSocket


# class WebSocketManager:
#     """
#     Manages active WebSocket connections.
#     """

#     def __init__(self):
#         self.active_connections: Dict[str, WebSocket] = {}

#     async def connect(self, request_id: str, websocket: WebSocket):
#         """
#         Accept a new WebSocket connection.
#         """

#         await websocket.accept()
#         self.active_connections[request_id] = websocket

#     def disconnect(self, request_id: str):
#         """
#         Remove connection when client disconnects.
#         """

#         if request_id in self.active_connections:
#             del self.active_connections[request_id]

#     async def send_event(self, request_id: str, event: dict):
#         """
#         Send event to a specific client.
#         """

#         websocket = self.active_connections.get(request_id)

#         if websocket:
#             await websocket.send_json(event)

#     async def broadcast(self, event: dict):
#         """
#         Send event to all connected clients.
#         """

#         for websocket in self.active_connections.values():
#             await websocket.send_json(event)


# # Global instance
# websocket_manager = WebSocketManager()