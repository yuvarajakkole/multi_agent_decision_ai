"""
agents/market_agent/graph.py

CONFIDENCE FROM TOOL DIRECTLY — no guessing from LLM output.
agent.py.run() returns (raw_str, tool_conf, tool_source).

BUG 1 FIX: was data.get("_data_source", "unknown") → always "unknown" → 0.0
BUG 2 FIX: skip MIN rule when retries==0 (LangGraph coerces None→0.0 in initial state)
"""

import json
import re
from datetime import datetime, timezone

from agents.market_agent.agent import run as run_market_agent
from config.settings import MAX_AGENT_RETRIES, MIN_CONFIDENCE
from streaming.streamer import stream_event

IGNORE_THRESHOLD = 0.40   # lowered: partial live data is still useful


def _parse_output(raw: str, market: str) -> tuple[dict, str]:
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
    return {
        "market":               market,
        "attractiveness_score": 0,
        "competition_level":    "Unknown",
        "go_signal":            "Hold",
        "data_quality":         "Low",
        "summary":              "Market analysis failed — parse error.",
        "_parse_error":         True,
    }, "fallback"


def _assess_quality(data: dict, tool_conf: float) -> tuple[float, list[str]]:
    """
    Confidence = tool_conf (real API quality) minus small penalties for LLM output gaps.
    Penalties are capped so a few missing LLM fields don't collapse real live data.
    """
    issues     = []
    confidence = tool_conf   # starts from real API confidence

    if data.get("_parse_error"):
        issues.append("[PARSE_ERROR] JSON parse failed")
        confidence = min(confidence, 0.30)
        return round(max(0.10, confidence), 3), issues

    # Only penalise fields the LLM must generate (not tool-provided macro numbers)
    llm_required = ["market_size", "competition_level", "attractiveness_score", "go_signal", "summary"]
    deduction = 0.0
    for f in llm_required:
        v = data.get(f)
        if v is None or v == "" or v == "N/A":
            issues.append(f"[MISSING] {f}")
            deduction += 0.03   # 0.03 per field

    # Cap total deduction at 0.12 so live data confidence isn't wiped by a few missing fields
    deduction  = min(deduction, 0.12)
    confidence -= deduction

    score = data.get("attractiveness_score")
    if score is not None and (not isinstance(score, (int, float)) or not (0 <= float(score) <= 100)):
        data["attractiveness_score"] = 0
        issues.append(f"[INVALID] attractiveness_score={score!r}")
        confidence -= 0.03

    return round(max(0.10, min(1.0, confidence)), 3), issues


async def market_agent_node(state: dict) -> dict:
    request_id = state["request_id"]
    user_query = state["user_query"]
    market     = state.get("market", "")
    budget     = float(state.get("budget", 0) or 0)
    timeline   = int(state.get("timeline_months", 12) or 12)
    retries    = int(state.get("market_retries", 0) or 0)

    # BUG 2 FIX: retries==0 → always None (don't trust LangGraph initial 0.0)
    raw_prev  = state.get("market_confidence")
    prev_conf = float(raw_prev) if (
        retries > 0 and raw_prev is not None and float(raw_prev or 0) > 0
    ) else None

    await stream_event(request_id, "agent_start", "market_agent",
                       f"Analysing market: {market} (attempt {retries + 1})")
    print(f"\n[market_agent] START  market={market}  retry={retries}  prev_conf={prev_conf}")

    prev_output = prev_issues = None
    if retries > 0:
        prev_data   = state.get("market_insights", {})
        prev_output = json.dumps(prev_data)
        prev_issues = state.get("quality_flags", {}).get("market_issues", [])

    # BUG 1 FIX: run() now returns (raw, tool_conf, tool_source)
    # tool_conf comes directly from World Bank envelope — not guessed from LLM output
    raw, tool_conf, tool_source = await run_market_agent(
        user_query      = user_query,
        market          = market,
        budget          = budget,
        timeline_months = timeline,
        previous_output = prev_output,
        quality_issues  = prev_issues,
    )

    data, parse_method = _parse_output(raw, market)
    confidence, issues = _assess_quality(data, tool_conf)

    # MIN rule: only on genuine retries
    if prev_conf is not None:
        new_conf = min(prev_conf, confidence)
        if new_conf < confidence:
            print(f"[market_agent] MIN rule: {prev_conf:.3f}→{confidence:.3f}→{new_conf:.3f}")
        confidence = new_conf

    needs_retry = (
        confidence < MIN_CONFIDENCE
        and retries < MAX_AGENT_RETRIES
        and len(issues) > 0
    )
    ignore = confidence < IGNORE_THRESHOLD

    print(
        f"[market_agent] conf={confidence:.3f}  tool_conf={tool_conf:.3f}  "
        f"source={tool_source}  score={data.get('attractiveness_score')}  "
        f"ignore={ignore}"
    )

    log_entry = {
        "agent":        "market_agent",
        "timestamp":    datetime.now(timezone.utc).isoformat(),
        "attempt":      retries + 1,
        "confidence":   confidence,
        "tool_conf":    tool_conf,
        "tool_source":  tool_source,
        "parse_method": parse_method,
        "issues":       issues,
        "will_retry":   needs_retry,
        "ignore":       ignore,
    }

    await stream_event(request_id, "agent_complete", "market_agent", {
        "confidence":  confidence,
        "tool_source": tool_source,
        "score":       data.get("attractiveness_score"),
        "go_signal":   data.get("go_signal"),
        "needs_retry": needs_retry,
        "ignore":      ignore,
    })
    print(f"[market_agent] END  conf={confidence:.3f}  score={data.get('attractiveness_score')}  ignore={ignore}")

    return {
        "market_insights":   data,
        "market_confidence": confidence,
        "market_retries":    retries + 1,
        "quality_flags": {
            "market_issues":      issues,
            "market_needs_retry": needs_retry,
            "market_ignore":      ignore,
            "market_source":      tool_source,
        },
        "execution_log": [log_entry],
    }
