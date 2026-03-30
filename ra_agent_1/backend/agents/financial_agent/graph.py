"""agents/financial_agent/graph.py — LangGraph node for financial agent."""

import json
from datetime import datetime, timezone

from agents.financial_agent.agent import run as run_financial_agent
from config.settings import MAX_AGENT_RETRIES, MIN_CONFIDENCE
from streaming.streamer import stream_event


def _assess_quality(data: dict) -> tuple:
    issues     = []
    confidence = 1.0

    required = [
        "estimated_roi_pct", "estimated_irr_pct",
        "payback_months", "risk_level", "inflation_pct",
    ]
    for f in required:
        v = data.get(f)
        if v is None:
            issues.append(f"Missing: {f}")
            confidence -= 0.12

    if data.get("_parse_error"):
        issues.append("JSON parse failed")
        confidence -= 0.30

    roi = data.get("estimated_roi_pct")
    if roi is not None and not isinstance(roi, (int, float)):
        issues.append("ROI is not a number")
        confidence -= 0.10

    irr = data.get("estimated_irr_pct")
    if irr is not None and isinstance(irr, (int, float)) and not -100 <= irr <= 1000:
        issues.append(f"IRR {irr}% implausible")
        confidence -= 0.10

    if data.get("data_quality") == "Low":
        confidence -= 0.08

    return round(max(0.0, min(1.0, confidence)), 3), issues


async def financial_agent_node(state: dict) -> dict:
    rid      = state["request_id"]
    retries  = int(state.get("financial_retries", 0))

    await stream_event(rid, "agent_start", "financial_agent",
                       f"Financial analysis: {state.get('market')} (attempt {retries + 1})")

    print(f"\n[financial_agent] START  market={state.get('market')}  retry={retries}")

    prev_output = None
    prev_issues = None
    if retries > 0:
        prev_output = json.dumps(state.get("financial_analysis", {}))
        prev_issues = state.get("quality_flags", {}).get("financial_issues", [])

    data, calcs = await run_financial_agent(
        user_query      = state["user_query"],
        market          = state.get("market", ""),
        budget          = float(state.get("budget", 1_000_000)),
        timeline_months = int(state.get("timeline_months", 12)),
        previous_output = prev_output,
        quality_issues  = prev_issues,
    )

    confidence, issues = _assess_quality(data)
    needs_retry = (
        confidence < MIN_CONFIDENCE
        and retries < MAX_AGENT_RETRIES
        and len(issues) > 0
    )

    print(f"[financial_agent] ROI={data.get('estimated_roi_pct')}%  "
          f"IRR={data.get('estimated_irr_pct')}%  "
          f"conf={confidence}  retry={needs_retry}")

    log_entry = {
        "agent":      "financial_agent",
        "timestamp":  datetime.now(timezone.utc).isoformat(),
        "attempt":    retries + 1,
        "confidence": confidence,
        "issues":     issues,
        "will_retry": needs_retry,
        "roi":        data.get("estimated_roi_pct"),
        "irr":        data.get("estimated_irr_pct"),
    }

    await stream_event(rid, "agent_complete", "financial_agent", {
        "roi":            data.get("estimated_roi_pct"),
        "irr":            data.get("estimated_irr_pct"),
        "attractiveness": data.get("financial_attractiveness"),
        "confidence":     confidence,
        "needs_retry":    needs_retry,
    })

    return {
        "financial_analysis":  data,
        "financial_confidence": confidence,
        "financial_retries":   retries + 1,
        "quality_flags": {
            "financial_issues":     issues,
            "financial_needs_retry": needs_retry,
        },
        "execution_log": [log_entry],
    }
