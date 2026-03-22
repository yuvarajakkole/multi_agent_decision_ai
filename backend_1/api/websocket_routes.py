# backend/api/websocket_routes.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from graph.graph_runner import run_graph

from streaming.websocket_manager import ws_manager

from utils.request_id import generate_request_id


router = APIRouter()


# ---------------------------------------------------------
# WEBSOCKET ROUTE
# ---------------------------------------------------------

@router.websocket("/ws/decision")

async def decision_websocket(websocket: WebSocket):

    await websocket.accept()

    request_id = generate_request_id()

    await ws_manager.connect(request_id, websocket)

    try:

        while True:

            data = await websocket.receive_json()

            user_query = data.get("user_query")

            market = data.get("market")

            state = {
                "request_id": request_id,
                "user_query": user_query,
                "market": market,
                "company_name": "RA Groups",
                "budget": data.get("budget", 1000000),
                "timeline_months": data.get("timeline_months", 12)
            }

            await run_graph(state)

    except WebSocketDisconnect:

        await ws_manager.disconnect(request_id)