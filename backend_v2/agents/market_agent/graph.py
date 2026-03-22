"""
Market Agent Node — validated output with reliability envelope.
Passes the actual product type (from user query) into tool calls.
"""
import json, re
from agents.market_agent.agent import run_market_agent
from core.reliability.validator import validate_agent_output
from core.trace.decision_trace import compact_input, compact_output
from streaming.agent_step_streamer import stream_agent_start, stream_agent_complete

_FALLBACK = lambda m: {
    "market": m, "gdp_growth_percent": "N/A", "inflation_percent": "N/A",
    "competition_level": "Medium", "market_attractiveness": "Unknown",
    "summary": "Market data could not be retrieved — manual review needed.",
}

def _parse(raw: str, market: str) -> tuple:
    try:
        d   = json.loads(raw.strip().replace("```json","").replace("```","").strip())
        src = "hybrid" if d.get("gdp_growth_percent") not in (None,"N/A","") else "fallback"
        return d, src
    except Exception:
        pass
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            d = json.loads(m.group())
            return d, "hybrid"
        except Exception:
            pass
    return _FALLBACK(market), "fallback"


async def market_agent_node(state: dict) -> dict:
    print("\n========== MARKET AGENT NODE START ==========")
    request_id = state["request_id"]
    user_query = state["user_query"]
    market     = state.get("market", "unknown")
    budget     = state.get("budget", 0)
    trace      = state.get("_trace")

    if trace:
        trace.start_step("market_agent")
    await stream_agent_start(request_id, "market_agent")

    raw = await run_market_agent(
        f"Market analysis for this specific query:\n"
        f"Query: {user_query}\n"
        f"Target Market/Country: {market}\n"
        f"Budget: ${budget:,.0f}\n\n"
        "IMPORTANT: Analyse the SPECIFIC product mentioned in the query, not generic fintech.\n"
        "Use ALL tools. Return structured JSON."
    )
    data, source = _parse(raw, market)

    envelope = validate_agent_output("market_agent","market_insights", data, source)
    print(f"Market confidence: {envelope['confidence']} | Errors: {envelope['errors']}")

    if trace:
        trace.log_step("market_agent", compact_input(state), compact_output(data),
                       envelope["confidence"], source, envelope["errors"], envelope["warnings"])

    await stream_agent_complete(request_id, "market_agent", {
        "market_attractiveness": data.get("market_attractiveness"),
        "confidence":            envelope["confidence"],
    })
    print("========== MARKET AGENT NODE END ==========\n")
    return {"market_insights": data, "_market_agent_envelope": envelope}
