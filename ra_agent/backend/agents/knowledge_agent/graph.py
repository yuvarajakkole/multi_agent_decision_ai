"""
agents/knowledge_agent/graph.py

BUG 2 FIX: prev_conf=0.0 from initial state → min(0.0, 1.0)=0.0 always.
Fix: skip MIN rule on first call (retries==0).

Knowledge agent reads from ra_groups_knowledge.json (curated internal data).
Base confidence = 0.75 (internal company data is reliable, not external static).
"""

import json
import re
from datetime import datetime, timezone

from agents.knowledge_agent.agent import run as run_knowledge_agent
from config.settings import MAX_AGENT_RETRIES, MIN_CONFIDENCE
from streaming.streamer import stream_event

IGNORE_THRESHOLD        = 0.50
_INTERNAL_BASE_CONF     = 0.75   # internal JSON file — reliable, curated

_SAFE_FALLBACK = {
    "company_name": "RA Groups",
    "strategic_fit": "Medium",
    "available_budget_usd": 0,
    "budget_within_policy": False,
    "max_policy_investment_usd": 5_000_000,
    "risk_appetite": "Medium",
    "company_strengths": [],
    "company_weaknesses": [],
    "past_expansions": [],
    "has_experience_in_this_market": False,
    "data_quality": "Low",
    "summary": "Knowledge analysis unavailable.",
    "_parse_error": True,
}


def _parse(raw: str) -> tuple[dict, str]:
    cleaned = raw.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned), "direct"
    except Exception:
        pass
    m = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if m:
        try:
            return json.loads(m.group()), "regex"
        except Exception:
            pass
    return dict(_SAFE_FALLBACK), "fallback"


def _assess_quality(data: dict) -> tuple[float, list[str]]:
    issues     = []
    confidence = _INTERNAL_BASE_CONF  # start from internal data base

    if data.get("_parse_error"):
        issues.append("[PARSE_ERROR] Parse failed — using fallback")
        confidence -= 0.45   # significant penalty for failing to read internal data

    if not data.get("company_strengths"):
        issues.append("[MISSING] company_strengths is empty")
        confidence -= 0.08

    if not data.get("past_expansions"):
        issues.append("[MISSING] past_expansions is empty")
        confidence -= 0.08

    strategic_fit = data.get("strategic_fit")
    if strategic_fit not in ("High", "Medium", "Low"):
        issues.append(f"[INVALID] strategic_fit={strategic_fit!r} → set Medium")
        data["strategic_fit"] = "Medium"
        confidence -= 0.06

    summary = data.get("summary", "")
    if not summary or len(summary) < 40:
        issues.append("[WEAK] Summary too short")
        confidence -= 0.05

    if data.get("data_quality") == "Low" and not data.get("_parse_error"):
        issues.append("[LOW_QUALITY] Self-reported Low quality")
        confidence -= 0.07

    # Sanitise budget field
    if data.get("available_budget_usd") is None:
        data["available_budget_usd"] = 0
        issues.append("[INVALID] available_budget_usd=None → 0")
        confidence -= 0.03

    return round(max(0.10, min(1.0, confidence)), 3), issues


async def knowledge_agent_node(state: dict) -> dict:
    rid     = state["request_id"]
    retries = int(state.get("knowledge_retries", 0) or 0)

    # BUG 2 FIX: don't apply MIN rule on first call
    raw_prev  = state.get("knowledge_confidence")
    prev_conf = float(raw_prev) if (retries > 0 and raw_prev is not None and float(raw_prev) > 0) else None

    await stream_event(rid, "agent_start", "knowledge_agent",
                       f"Internal analysis (attempt {retries + 1})")
    print(f"\n[knowledge_agent] START  retry={retries}  prev_conf={prev_conf}")

    prev_output = None
    prev_issues = None
    if retries > 0:
        prev_output = json.dumps(state.get("knowledge_summary", {}))
        prev_issues = state.get("quality_flags", {}).get("knowledge_issues", [])

    raw = await run_knowledge_agent(
        user_query      = state["user_query"],
        market          = state.get("market", ""),
        budget          = float(state.get("budget", 0) or 0),
        timeline_months = int(state.get("timeline_months", 12) or 12),
        previous_output = prev_output,
        quality_issues  = prev_issues,
    )

    data, parse_method = _parse(raw)
    confidence, issues = _assess_quality(data)

    if prev_conf is not None:
        if confidence < prev_conf:
            print(f"[knowledge_agent] MIN rule: {prev_conf:.3f} → {confidence:.3f}")
        confidence = min(prev_conf, confidence)

    needs_retry = (
        confidence < MIN_CONFIDENCE
        and retries < MAX_AGENT_RETRIES
        and len(issues) > 0
    )
    ignore = confidence < IGNORE_THRESHOLD

    print(f"[knowledge_agent] fit={data.get('strategic_fit')}  conf={confidence}  ignore={ignore}")

    log_entry = {
        "agent":        "knowledge_agent",
        "timestamp":    datetime.now(timezone.utc).isoformat(),
        "attempt":      retries + 1,
        "confidence":   confidence,
        "prev_conf":    prev_conf,
        "source":       "internal_json",
        "parse_method": parse_method,
        "issues":       issues,
        "will_retry":   needs_retry,
        "ignore":       ignore,
    }

    await stream_event(rid, "agent_complete", "knowledge_agent", {
        "strategic_fit":  data.get("strategic_fit"),
        "has_experience": data.get("has_experience_in_this_market"),
        "confidence":     confidence,
        "needs_retry":    needs_retry,
        "ignore":         ignore,
    })

    print(f"[knowledge_agent] END  conf={confidence}")
    return {
        "knowledge_summary":    data,
        "knowledge_confidence": confidence,
        "knowledge_retries":    retries + 1,
        "quality_flags": {
            "knowledge_issues":      issues,
            "knowledge_needs_retry": needs_retry,
            "knowledge_ignore":      ignore,
            "knowledge_source":      "internal_json",
        },
        "execution_log": [log_entry],
    }
