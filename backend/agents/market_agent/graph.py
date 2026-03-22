import json
import re
from agents.market_agent.agent import run_market_agent
from streaming.agent_step_streamer import stream_agent_start, stream_agent_complete


async def market_agent_node(state: dict) -> dict:

    print("\n========== MARKET AGENT NODE START ==========")

    request_id = state["request_id"]
    user_query = state["user_query"]
    market     = state.get("market", "unknown market")
    budget     = state.get("budget", 0)

    await stream_agent_start(request_id, "market_agent")

    raw = await run_market_agent(
        f"Analyze the market for this business decision:\n"
        f"Query: {user_query}\n"
        f"Target Market: {market}\n"
        f"Budget: ${budget:,.0f}\n\n"
        "Use your tools to gather market size, competitor, regulatory, "
        "and trend data. Then return the JSON output."
    )

    print(f"Market agent raw output: {raw}")
    market_insights = _parse_json(raw, market)

    await stream_agent_complete(request_id, "market_agent", market_insights)
    print("========== MARKET AGENT NODE END ==========\n")

    return {"market_insights": market_insights}


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
        "market": market, "product": "unknown",
        "market_size_usd": "Data unavailable", "growth_rate_percent": "Data unavailable",
        "competition_level": "Medium", "key_competitors": [],
        "regulatory_environment": "Neutral", "key_regulatory_notes": "Requires further research",
        "market_trends": [], "market_attractiveness": "Medium",
        "summary": "Market analysis could not be fully completed."
    }