"""
agents/market_agent/graph.py

LangGraph node for the market agent.
Handles:
  - First-run execution
  - Retry loops when quality is insufficient
  - Writing confidence + quality flags back to shared state
"""

import json
import re
from datetime import datetime, timezone

from agents.market_agent.agent import run as run_market_agent
from config.settings import MAX_AGENT_RETRIES, MIN_CONFIDENCE
from streaming.streamer import stream_event


def _parse_output(raw: str, market: str) -> tuple[dict, str]:
    """Parse JSON from LLM output. Returns (data, parse_method)."""
    cleaned = raw.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned), "direct"
    except Exception:
        pass
    m = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if m:
        try:
            return json.loads(m.group()), "regex_extract"
        except Exception:
            pass
    # Fallback
    return {
        "market": market,
        "product_class": "lending",
        "attractiveness_score": 50,
        "competition_level": "Medium",
        "go_signal": "Hold",
        "data_quality": "Low",
        "summary": "Market analysis failed — data unavailable.",
        "_parse_error": True,
    }, "fallback"


def _assess_quality(data: dict) -> tuple[float, list]:
    """
    Assess data quality. Returns (confidence 0-1, list of issues).
    Issues trigger retry loops in the graph router.
    """
    issues = []
    confidence = 1.0

    required = [
        "gdp_growth_pct", "inflation_pct", "lending_rate_pct",
        "market_size", "competition_level", "attractiveness_score",
    ]
    for f in required:
        v = data.get(f)
        if v is None or v == "" or v == "N/A":
            issues.append(f"Missing field: {f}")
            confidence -= 0.12

    if data.get("_parse_error"):
        issues.append("JSON parse failed")
        confidence -= 0.25

    if data.get("data_quality") == "Low":
        issues.append("Data quality low — all fallback values used")
        confidence -= 0.10

    score = data.get("attractiveness_score", 50)
    if not isinstance(score, (int, float)) or not (0 <= score <= 100):
        issues.append(f"attractiveness_score {score} out of range")
        confidence -= 0.10

    # Penalise obviously generic answers
    summary = data.get("summary", "")
    if len(summary) < 30:
        issues.append("Summary too short — likely generic")
        confidence -= 0.08

    return round(max(0.0, min(1.0, confidence)), 3), issues


async def market_agent_node(state: dict) -> dict:
    """
    LangGraph node. Called on first run AND on retry loops.
    Writes: market_insights, market_confidence, quality_flags, execution_log
    """
    request_id = state["request_id"]
    user_query = state["user_query"]
    market     = state.get("market", "")
    budget     = float(state.get("budget", 1_000_000))
    timeline   = int(state.get("timeline_months", 12))
    retries    = int(state.get("market_retries", 0))

    await stream_event(request_id, "agent_start", "market_agent",
                       f"Analysing market: {market} (attempt {retries + 1})")

    print(f"\n[market_agent] START  market={market}  retry={retries}")

    # Get previous output if this is a retry
    prev_output = None
    prev_issues = None
    if retries > 0:
        prev_data   = state.get("market_insights", {})
        prev_output = json.dumps(prev_data)
        prev_issues = state.get("quality_flags", {}).get("market_issues", [])

    raw = await run_market_agent(
        user_query    = user_query,
        market        = market,
        budget        = budget,
        timeline_months = timeline,
        previous_output = prev_output,
        quality_issues  = prev_issues,
    )

    data, parse_method = _parse_output(raw, market)
    confidence, issues = _assess_quality(data)

    # Determine if we need to retry
    needs_retry = (
        confidence < MIN_CONFIDENCE
        and retries < MAX_AGENT_RETRIES
        and len(issues) > 0
    )

    print(f"[market_agent] confidence={confidence}  issues={issues}  needs_retry={needs_retry}")

    log_entry = {
        "agent":       "market_agent",
        "timestamp":   datetime.now(timezone.utc).isoformat(),
        "attempt":     retries + 1,
        "confidence":  confidence,
        "issues":      issues,
        "parse_method": parse_method,
        "will_retry":  needs_retry,
    }

    await stream_event(request_id, "agent_complete", "market_agent", {
        "confidence":  confidence,
        "score":       data.get("attractiveness_score"),
        "go_signal":   data.get("go_signal"),
        "needs_retry": needs_retry,
        "issues":      issues[:2] if issues else [],
    })

    print(f"[market_agent] END  confidence={confidence}  score={data.get('attractiveness_score')}")

    return {
        "market_insights":    data,
        "market_confidence":  confidence,
        "market_retries":     retries + 1,
        "quality_flags":      {"market_issues": issues, "market_needs_retry": needs_retry},
        "execution_log":      [log_entry],
    }
