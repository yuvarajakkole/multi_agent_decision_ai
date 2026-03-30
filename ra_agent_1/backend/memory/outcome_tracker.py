"""memory/outcome_tracker.py — Learning memory loop."""

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

_PATH = Path(__file__).resolve().parent / "decision_history.json"
_lock = threading.Lock()


def _load() -> list:
    if _PATH.exists():
        try:
            return json.loads(_PATH.read_text())
        except Exception:
            pass
    return []


def _save(data: list):
    _PATH.write_text(json.dumps(data, indent=2))


def save_decision(request_id, user_query, market, decision, confidence, score, agent_confs):
    with _lock:
        h = _load()
        h.append({
            "request_id":    request_id,
            "timestamp":     datetime.now(timezone.utc).isoformat(),
            "user_query":    user_query,
            "market":        market.lower(),
            "decision":      decision,
            "confidence":    confidence,
            "score":         score,
            "agent_confs":   agent_confs,
            "actual_outcome": None,
        })
        _save(h)


def record_outcome(request_id: str, outcome: str, notes: str = ""):
    with _lock:
        h = _load()
        for e in h:
            if e.get("request_id") == request_id:
                e["actual_outcome"] = outcome
                e["outcome_notes"]  = notes
                break
        _save(h)


def confidence_adjustment(market: str) -> float:
    """
    Adjust confidence based on past outcome accuracy for this market.
    +0.05 if historically accurate, -0.10 if historically inaccurate.
    """
    with _lock:
        h = _load()
    cases = [c for c in h
             if c.get("market", "").lower() == market.lower()
             and c.get("actual_outcome")]
    if not cases:
        return 0.0
    success_rate = sum(1 for c in cases if c["actual_outcome"] == "success") / len(cases)
    if success_rate >= 0.80:
        return +0.05
    if success_rate >= 0.60:
        return 0.0
    return -0.10


def get_summary() -> dict:
    with _lock:
        h = _load()
    if not h:
        return {"total": 0}
    by_d = {}
    for e in h:
        d = e.get("decision", "?")
        by_d[d] = by_d.get(d, 0) + 1
    return {
        "total":           len(h),
        "by_decision":     by_d,
        "avg_confidence":  round(sum(e.get("confidence", 0) for e in h) / len(h), 3),
    }
