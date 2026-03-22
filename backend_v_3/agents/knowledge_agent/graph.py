import json, re
from agents.knowledge_agent.agent import run_knowledge_agent
from core.reliability.validator import validate_agent_output
from core.trace.decision_trace import compact_input, compact_output
from streaming.agent_step_streamer import stream_agent_start, stream_agent_complete

_FALLBACK = {
    "company_name": "RA Groups", "strategic_fit": "Medium",
    "available_budget_usd": 3_000_000, "budget_within_limits": True,
    "max_allowed_investment_usd": 5_000_000,
    "risk_appetite_match": "Aligned", "company_strengths": [],
    "company_weaknesses": [], "relevant_past_expansions": [],
    "strategic_objectives_alignment": [],
    "live_industry_context": "N/A",
    "recommendation_from_knowledge": "Manual review recommended.",
    "summary": "Internal knowledge assessment could not be completed.",
}

def _parse(raw: str) -> tuple:
    try:
        d = json.loads(raw.strip().replace("```json","").replace("```","").strip())
        return d, "hybrid"
    except Exception:
        pass
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try: return json.loads(m.group()), "hybrid"
        except Exception: pass
    return _FALLBACK.copy(), "fallback"


async def knowledge_agent_node(state: dict) -> dict:
    print("\n========== KNOWLEDGE AGENT NODE START ==========")
    request_id = state["request_id"]
    market     = state.get("market", "unknown")
    trace      = state.get("_trace")

    if trace: trace.start_step("knowledge_agent")
    await stream_agent_start(request_id, "knowledge_agent")

    raw  = await run_knowledge_agent(
        f"Strategic fit analysis:\nQuery: {state['user_query']}\n"
        f"Market: {market}\nBudget: ${state.get('budget',0):,.0f}\n"
        "Use ALL tools. Return structured JSON."
    )
    data, source = _parse(raw)

    envelope = validate_agent_output("knowledge_agent","knowledge_summary", data, source)
    print(f"Knowledge confidence: {envelope['confidence']} | Errors: {envelope['errors']}")

    if trace:
        trace.log_step("knowledge_agent", compact_input(state), compact_output(data),
                       envelope["confidence"], source, envelope["errors"], envelope["warnings"])

    await stream_agent_complete(request_id, "knowledge_agent",
                                {"strategic_fit": data.get("strategic_fit"),
                                 "confidence": envelope["confidence"]})
    print("========== KNOWLEDGE AGENT NODE END ==========\n")
    return {"knowledge_summary": data, "_knowledge_agent_envelope": envelope}
