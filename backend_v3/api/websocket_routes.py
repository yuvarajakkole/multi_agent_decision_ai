from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from graph.graph_runner import run_graph
from streaming.websocket_manager import ws_manager
from utils.request_id import generate_request_id

router = APIRouter()

@router.websocket("/ws/decision")
async def decision_ws(websocket: WebSocket):
    rid = generate_request_id()
    await ws_manager.connect(rid, websocket)
    try:
        while True:
            data = await websocket.receive_json()
            state = {
                "request_id":     rid,
                "user_query":     data.get("user_query", ""),
                "market":         data.get("market", ""),
                "company_name":   data.get("company_name", "RA Groups"),
                "budget":         data.get("budget", 1_000_000),
                "timeline_months": data.get("timeline_months", 12),
            }
            await run_graph(state)
    except WebSocketDisconnect:
        await ws_manager.disconnect(rid)
