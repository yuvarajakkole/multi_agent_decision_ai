"""
core/trace/decision_trace.py
Full step-by-step explainability trace.  One instance per request.
Attached to AgentState as _trace, serialised to _decision_trace for API response.
"""
import time
from datetime import datetime, timezone


class DecisionTrace:
    def __init__(self, request_id: str, user_query: str, market: str):
        self.request_id = request_id
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.user_query = user_query
        self.market     = market
        self.steps: list = []
        self._timers: dict = {}

    def start_step(self, agent: str):
        self._timers[agent] = time.monotonic()

    def log_step(self, agent, input_summary, output_summary,
                 confidence, source, errors, warnings):
        elapsed = round(time.monotonic() - self._timers.get(agent, time.monotonic()), 3)
        self.steps.append({
            "step":           len(self.steps) + 1,
            "agent":          agent,
            "timestamp":      datetime.now(timezone.utc).isoformat(),
            "duration_sec":   elapsed,
            "input_summary":  input_summary,
            "output_summary": output_summary,
            "confidence":     confidence,
            "source":         source,
            "errors":         errors,
            "warnings":       warnings,
            "status":         "ok" if not errors else "degraded",
        })

    def to_dict(self) -> dict:
        return {
            "request_id":  self.request_id,
            "user_query":  self.user_query,
            "market":      self.market,
            "started_at":  self.started_at,
            "ended_at":    datetime.now(timezone.utc).isoformat(),
            "total_steps": len(self.steps),
            "steps":       self.steps,
        }


def compact_input(state: dict) -> dict:
    return {k: state.get(k) for k in ("user_query","market","budget","timeline_months")}


def compact_output(data: dict, n: int = 6) -> dict:
    if not isinstance(data, dict): return {}
    keys = list(data.keys())[:n]
    return {k: data[k] for k in keys}
