"""
backend/main.py — FastAPI application entry point.

Fix: budget/timeline no longer default to 1_000_000 / 12 in this layer.
     Supervisor extracts from query; runner receives 0 as explicit "not provided".
"""

import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config.settings      import API_HOST, API_PORT, CORS_ORIGINS, DEBUG
from config.langsmith_config import enable_tracing
from schemas.api_models   import DecisionRequest, OutcomeRequest
from graph.graph_runner   import run as run_graph
from memory.outcome_tracker import record_outcome, get_summary
from streaming.streamer   import register, unregister
from utils.request_id     import new_id

# Structured logging
logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    datefmt = "%H:%M:%S",
)
log = logging.getLogger("main")

app = FastAPI(
    title       = "RA Agent System",
    description = "Multi-Agent Decision Intelligence Platform",
    version     = "3.1",
    docs_url    = "/docs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins     = CORS_ORIGINS + ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)


@app.on_event("startup")
async def startup():
    client = enable_tracing()
    log.info("RA Agent System v3.1 started  docs=http://%s:%s/docs", API_HOST, API_PORT)
    if client:
        log.info("LangSmith tracing enabled")


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "3.1"}


@app.get("/api/history")
def history():
    return get_summary()


@app.post("/api/decision")
async def decision(req: DecisionRequest):
    rid = new_id()
    # Pass 0 for budget/timeline when not provided — supervisor extracts from query
    result = await run_graph(
        user_query      = req.user_query,
        market          = req.market or "",
        budget          = req.budget or 0,           # ← no default 1_000_000
        timeline_months = req.timeline_months or 0,  # ← no default 12
        company_name    = req.company_name or "RA Groups",
        request_id      = rid,
    )
    return result


@app.post("/api/outcome")
def outcome(req: OutcomeRequest):
    record_outcome(req.request_id, req.actual_outcome, req.notes or "")
    return {"status": "recorded", "request_id": req.request_id}


@app.websocket("/ws/decision")
async def ws_decision(ws: WebSocket):
    rid = new_id()
    await register(rid, ws)
    try:
        while True:
            data = await ws.receive_json()
            await run_graph(
                user_query      = data.get("user_query", ""),
                market          = data.get("market", ""),
                budget          = float(data.get("budget", 0)),
                timeline_months = int(data.get("timeline_months", 0)),
                company_name    = data.get("company_name", "RA Groups"),
                request_id      = rid,
            )
    except WebSocketDisconnect:
        await unregister(rid)
