"""
agents/financial_agent/graph.py

Confidence now comes directly from the tool (get_macro_indicators returns
the World Bank envelope confidence). No more guessing from LLM output.
BUG 2 FIX: skip MIN rule on first call (retries==0).
"""

import json
from datetime import datetime, timezone

from agents.financial_agent.agent import run as run_financial_agent
from config.settings import MAX_AGENT_RETRIES, MIN_CONFIDENCE
from streaming.streamer import stream_event

IGNORE_THRESHOLD = 0.40


def _assess_quality(data: dict, tool_conf: float) -> tuple[float, list[str]]:
    issues     = []
    confidence = max(tool_conf, 0.35)   # deterministic calcs always worth something

    if data.get("_parse_error"):
        issues.append("[PARSE_ERROR]")
        confidence = min(confidence, 0.40)

    required = ["estimated_roi_pct", "estimated_irr_pct", "payback_months", "risk_level"]
    for f in required:
        if data.get(f) is None:
            issues.append(f"[MISSING] {f}")
            confidence -= 0.03

    roi = data.get("estimated_roi_pct")
    if roi is not None and not isinstance(roi, (int, float)):
        data["estimated_roi_pct"] = 0.0
        issues.append(f"[INVALID] ROI={roi!r}")
        confidence -= 0.03

    irr = data.get("estimated_irr_pct")
    if irr is not None and isinstance(irr, (int, float)) and not (-100 <= float(irr) <= 1000):
        data["estimated_irr_pct"] = 0.0
        issues.append(f"[INVALID] IRR={irr}%")
        confidence -= 0.03

    return round(max(0.15, min(1.0, confidence)), 3), issues


async def financial_agent_node(state: dict) -> dict:
    rid     = state["request_id"]
    retries = int(state.get("financial_retries", 0) or 0)

    # BUG 2 FIX: skip MIN on first call
    raw_prev  = state.get("financial_confidence")
    prev_conf = float(raw_prev) if (retries > 0 and raw_prev is not None
                                    and float(raw_prev) > 0) else None

    market = state.get("market", "")
    await stream_event(rid, "agent_start", "financial_agent",
                       f"Financial analysis: {market} (attempt {retries + 1})")
    print(f"\n[financial_agent] START  market={market}  retry={retries}  prev_conf={prev_conf}")

    prev_output = None
    prev_issues = None
    if retries > 0:
        prev_output = json.dumps(state.get("financial_analysis", {}))
        prev_issues = state.get("quality_flags", {}).get("financial_issues", [])

    # run() now returns (merged_data, calcs, tool_conf, tool_source)
    data, calcs, tool_conf, tool_source = await run_financial_agent(
        user_query      = state["user_query"],
        market          = market,
        budget          = float(state.get("budget", 0) or 0),
        timeline_months = int(state.get("timeline_months", 12) or 12),
        previous_output = prev_output,
        quality_issues  = prev_issues,
    )

    confidence, issues = _assess_quality(data, tool_conf)

    if prev_conf is not None:
        new_conf = min(prev_conf, confidence)
        if new_conf < confidence:
            print(f"[financial_agent] MIN rule: {prev_conf:.3f}→{confidence:.3f}→{new_conf:.3f}")
        confidence = new_conf

    needs_retry = (
        confidence < MIN_CONFIDENCE
        and retries < MAX_AGENT_RETRIES
        and len(issues) > 0
    )
    ignore = confidence < IGNORE_THRESHOLD

    print(
        f"[financial_agent] ROI={data.get('estimated_roi_pct')}%  "
        f"IRR={data.get('estimated_irr_pct')}%  "
        f"conf={confidence:.3f}  tool_conf={tool_conf:.3f}  source={tool_source}  ignore={ignore}"
    )

    log_entry = {
        "agent":        "financial_agent",
        "timestamp":    datetime.now(timezone.utc).isoformat(),
        "attempt":      retries + 1,
        "confidence":   confidence,
        "tool_conf":    tool_conf,
        "tool_source":  tool_source,
        "issues":       issues,
        "will_retry":   needs_retry,
        "ignore":       ignore,
        "roi":          data.get("estimated_roi_pct"),
        "irr":          data.get("estimated_irr_pct"),
    }

    await stream_event(rid, "agent_complete", "financial_agent", {
        "roi":         data.get("estimated_roi_pct"),
        "irr":         data.get("estimated_irr_pct"),
        "confidence":  confidence,
        "tool_source": tool_source,
        "needs_retry": needs_retry,
        "ignore":      ignore,
    })

    return {
        "financial_analysis":   data,
        "financial_confidence": confidence,
        "financial_retries":    retries + 1,
        "quality_flags": {
            "financial_issues":      issues,
            "financial_needs_retry": needs_retry,
            "financial_ignore":      ignore,
            "financial_source":      tool_source,
        },
        "execution_log": [log_entry],
    }
