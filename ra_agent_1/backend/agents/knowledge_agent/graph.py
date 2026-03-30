"""agents/knowledge_agent/graph.py — LangGraph node for knowledge agent."""

import json
import re
from datetime import datetime, timezone

from agents.knowledge_agent.agent import run as run_knowledge_agent
from config.settings import MAX_AGENT_RETRIES, MIN_CONFIDENCE
from streaming.streamer import stream_event

_FALLBACK = {
    "company_name": "RA Groups", "strategic_fit": "Medium",
    "available_budget_usd": 3_000_000, "budget_within_policy": True,
    "max_policy_investment_usd": 5_000_000, "risk_appetite": "Medium",
    "risk_appetite_match": "Aligned", "company_strengths": [],
    "company_weaknesses": [], "past_expansions": [],
    "has_experience_in_this_market": False, "data_quality": "Low",
    "summary": "Knowledge analysis unavailable.",
}


def _parse(raw: str) -> tuple:
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
    return dict(_FALLBACK), "fallback"


def _assess_quality(data: dict) -> tuple:
    issues     = []
    confidence = 1.0

    if not data.get("company_strengths"):
        issues.append("company_strengths is empty — use core_segments from tools")
        confidence -= 0.12

    if not data.get("past_expansions"):
        issues.append("past_expansions is empty — check load_past_expansions tool")
        confidence -= 0.12

    if not data.get("kpi_benchmarks"):
        issues.append("kpi_benchmarks missing — check load_financial_health tool")
        confidence -= 0.08

    if data.get("strategic_fit") not in ("High", "Medium", "Low"):
        issues.append("strategic_fit must be High|Medium|Low")
        confidence -= 0.10

    if not data.get("summary") or len(data.get("summary", "")) < 40:
        issues.append("Summary too short or missing")
        confidence -= 0.08

    if data.get("data_quality") == "Low":
        confidence -= 0.10

    return round(max(0.0, min(1.0, confidence)), 3), issues


async def knowledge_agent_node(state: dict) -> dict:
    rid     = state["request_id"]
    retries = int(state.get("knowledge_retries", 0))

    await stream_event(rid, "agent_start", "knowledge_agent",
                       f"Internal analysis (attempt {retries + 1})")
    print(f"\n[knowledge_agent] START  retry={retries}")

    prev_output = None
    prev_issues = None
    if retries > 0:
        prev_output = json.dumps(state.get("knowledge_summary", {}))
        prev_issues = state.get("quality_flags", {}).get("knowledge_issues", [])

    raw = await run_knowledge_agent(
        user_query      = state["user_query"],
        market          = state.get("market", ""),
        budget          = float(state.get("budget", 1_000_000)),
        timeline_months = int(state.get("timeline_months", 12)),
        previous_output = prev_output,
        quality_issues  = prev_issues,
    )

    data, parse_method = _parse(raw)
    confidence, issues = _assess_quality(data)
    needs_retry = (
        confidence < MIN_CONFIDENCE
        and retries < MAX_AGENT_RETRIES
        and len(issues) > 0
    )

    print(f"[knowledge_agent] fit={data.get('strategic_fit')}  "
          f"conf={confidence}  retry={needs_retry}")

    log_entry = {
        "agent":        "knowledge_agent",
        "timestamp":    datetime.now(timezone.utc).isoformat(),
        "attempt":      retries + 1,
        "confidence":   confidence,
        "issues":       issues,
        "parse_method": parse_method,
        "will_retry":   needs_retry,
    }

    await stream_event(rid, "agent_complete", "knowledge_agent", {
        "strategic_fit":   data.get("strategic_fit"),
        "has_experience":  data.get("has_experience_in_this_market"),
        "confidence":      confidence,
        "needs_retry":     needs_retry,
    })

    print(f"[knowledge_agent] END  conf={confidence}")
    return {
        "knowledge_summary":    data,
        "knowledge_confidence": confidence,
        "knowledge_retries":    retries + 1,
        "quality_flags": {
            "knowledge_issues":     issues,
            "knowledge_needs_retry": needs_retry,
        },
        "execution_log": [log_entry],
    }
