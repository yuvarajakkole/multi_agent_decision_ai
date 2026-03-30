"""streaming/streamer.py — WebSocket event streamer."""

import asyncio
from typing import Any, Dict
from fastapi import WebSocket


# ─── Connection registry ──────────────────────────────────────────────────────

_connections: Dict[str, WebSocket] = {}
_lock = asyncio.Lock()


async def register(request_id: str, ws: WebSocket):
    await ws.accept()
    async with _lock:
        _connections[request_id] = ws


async def unregister(request_id: str):
    async with _lock:
        _connections.pop(request_id, None)


def get_ws(request_id: str):
    return _connections.get(request_id)


# ─── Event senders ────────────────────────────────────────────────────────────

async def stream_event(
    request_id: str,
    event_type: str,
    agent: str,
    payload: Any = None,
):
    """Send a structured event to the WebSocket client."""
    ws = get_ws(request_id)
    if not ws:
        return
    msg = {
        "event":   event_type,
        "agent":   agent,
        "payload": payload if isinstance(payload, dict) else {"message": str(payload)},
    }
    try:
        await ws.send_json(msg)
    except Exception:
        pass


async def stream_final(
    request_id: str,
    decision: dict,
    report: str,
    weighted_confidence: float,
    confidence_label: str,
):
    """Send the final result event."""
    ws = get_ws(request_id)
    if not ws:
        return
    msg = {
        "event": "final_result",
        "payload": {
            "decision":            decision.get("decision"),
            "score":               decision.get("adjusted_score"),
            "confidence":          weighted_confidence,
            "confidence_label":    confidence_label,
            "report_markdown":     report,
            "rationale":           decision.get("rationale", []),
            "key_risks":           decision.get("key_risks", []),
            "next_steps":          decision.get("next_steps", []),
        },
    }
    try:
        await ws.send_json(msg)
    except Exception:
        pass
