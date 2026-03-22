from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from graph.graph_runner import run_graph
from streaming.websocket_manager import ws_manager
from utils.request_id import generate_request_id

router = APIRouter()


# ---------------------------------------------------------
# WEBSOCKET ROUTE
# FIX: websocket.accept() is called HERE in the route handler,
#      then ws_manager.connect() registers without calling accept again.
#      Old code called accept() inside ws_manager.connect() AND
#      the route had an implicit accept — causing double-accept errors.
# ---------------------------------------------------------

@router.websocket("/ws/decision")
async def decision_websocket(websocket: WebSocket):

    await websocket.accept()

    request_id = generate_request_id()
    await ws_manager.connect(request_id, websocket)

    # Immediately tell the client their request_id
    await websocket.send_json({
        "event": "connected",
        "request_id": request_id,
        "message": "Connected to RA Agent System. Send your query."
    })

    try:
        while True:
            data = await websocket.receive_json()

            user_query      = data.get("user_query", "")
            market          = data.get("market", "")
            budget          = float(data.get("budget", 1_000_000))
            timeline_months = int(data.get("timeline_months", 12))
            company_name    = data.get("company_name", "RA Groups")

            if not user_query or not market:
                await websocket.send_json({
                    "event": "error",
                    "message": "Both 'user_query' and 'market' fields are required."
                })
                continue

            state = {
                "request_id":      request_id,
                "user_query":      user_query,
                "market":          market,
                "company_name":    company_name,
                "budget":          budget,
                "timeline_months": timeline_months,
            }

            await run_graph(state)

    except WebSocketDisconnect:
        await ws_manager.disconnect(request_id)

    except Exception as e:
        print(f"WebSocket error [{request_id}]: {e}")
        try:
            await websocket.send_json({
                "event": "error",
                "message": f"Internal server error: {str(e)}"
            })
        except Exception:
            pass
        await ws_manager.disconnect(request_id)
