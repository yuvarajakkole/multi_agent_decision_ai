"""
memory/outcome_tracker.py
Stores every decision.  Enables learning: past failures reduce current confidence.
"""
import json
import threading
from pathlib import Path
from datetime import datetime, timezone

_PATH = Path(__file__).resolve().parent / "decision_history.json"
_lock = threading.Lock()


def _load() -> list:
    if _PATH.exists():
        try:
            return json.loads(_PATH.read_text())
        except Exception:
            return []
    return []


def _save(data: list):
    _PATH.write_text(json.dumps(data, indent=2))


def save_decision(request_id, user_query, market, decision,
                  confidence, total_score, agent_confidences):
    entry = {
        "request_id":        request_id,
        "timestamp":         datetime.now(timezone.utc).isoformat(),
        "user_query":        user_query,
        "market":            market.lower(),
        "decision":          decision,
        "confidence":        confidence,
        "total_score":       total_score,
        "agent_confidences": agent_confidences,
        "actual_outcome":    None,
        "outcome_notes":     "",
    }
    with _lock:
        history = _load()
        history.append(entry)
        _save(history)


def get_similar_cases(market: str, top_n: int = 5) -> list:
    with _lock:
        history = _load()
    matching = [h for h in history
                if h.get("market","").lower() == market.lower()
                and h.get("actual_outcome") is not None]
    matching.sort(key=lambda x: x.get("timestamp",""), reverse=True)
    return matching[:top_n]


def compute_confidence_adjustment(market: str) -> float:
    """
    Learning loop: past failures → reduce confidence of current run.
    Returns float in range [-0.15, +0.05].
    """
    cases    = get_similar_cases(market)
    outcomes = [c["actual_outcome"] for c in cases if c.get("actual_outcome")]
    if not outcomes:
        return 0.0
    rate = sum(1 for o in outcomes if o == "success") / len(outcomes)
    if rate >= 0.8:  return +0.05
    if rate >= 0.6:  return  0.0
    if rate >= 0.4:  return -0.08
    return -0.15


def record_outcome(request_id: str, actual_outcome: str, notes: str = ""):
    with _lock:
        history = _load()
        for e in history:
            if e.get("request_id") == request_id:
                e["actual_outcome"] = actual_outcome
                e["outcome_notes"]  = notes
                break
        _save(history)


def get_history_summary() -> dict:
    with _lock:
        history = _load()
    if not history:
        return {"total": 0, "by_decision": {}, "by_market": {}, "avg_confidence": 0}
    by_d = {}
    by_m = {}
    for h in history:
        by_d[h.get("decision","?")] = by_d.get(h.get("decision","?"), 0) + 1
        by_m[h.get("market","?")]   = by_m.get(h.get("market","?"),   0) + 1
    return {
        "total": len(history), "by_decision": by_d, "by_market": by_m,
        "avg_confidence": round(sum(h.get("confidence",0) for h in history) / len(history), 3),
    }
