import json
import re
from agents.financial_agent.agent import run_financial_agent
from streaming.agent_step_streamer import stream_agent_start, stream_agent_complete


async def financial_agent_node(state: dict) -> dict:

    print("\n========== FINANCIAL AGENT NODE START ==========")

    request_id      = state["request_id"]
    user_query      = state["user_query"]
    market          = state.get("market", "unknown market")
    budget          = state.get("budget", 1_000_000)
    timeline_months = state.get("timeline_months", 12)

    await stream_agent_start(request_id, "financial_agent")

    raw = await run_financial_agent(
        f"Evaluate the financial feasibility of this expansion:\n"
        f"Query: {user_query}\n"
        f"Target Market: {market}\n"
        f"Budget: ${budget:,.0f}\n"
        f"Timeline: {timeline_months} months\n\n"
        "Use your tools to gather macro indicators, estimate ROI, "
        "and assess credit risk. Then return the JSON output."
    )

    print(f"Financial agent raw output: {raw}")
    financial_analysis = _parse_json(raw, market)

    await stream_agent_complete(request_id, "financial_agent", financial_analysis)
    print("========== FINANCIAL AGENT NODE END ==========\n")

    return {"financial_analysis": financial_analysis}


def _parse_json(raw: str, market: str) -> dict:
    try:
        cleaned = raw.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except Exception:
        pass
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return {
        "market": market, "estimated_roi_percent": 0, "estimated_irr_percent": 0,
        "payback_period_months": 36, "risk_level": "High",
        "risk_factors": ["Insufficient data"], "meets_roi_threshold": False,
        "meets_irr_threshold": False, "macro_indicators": {},
        "financial_attractiveness": "Low",
        "summary": "Financial analysis could not be fully completed."
    }