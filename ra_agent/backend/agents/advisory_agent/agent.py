"""
agents/advisory_agent/agent.py

Handles open-ended advisory queries like:
- "Which field should I open a startup in India?"
- "Give me ideas for investment in Africa"
- "Where should I invest?"

These are NOT GO/NO_GO decisions — they need a consultative response
that recommends 3-5 specific opportunities with brief analysis of each.
"""

import json
from langchain_core.messages import SystemMessage, HumanMessage
from config.llm_config import get_reason_llm
from core.reliability.market_data import get_macro, get_market_profile, iso_code
from streaming.streamer import stream_event

_SYSTEM = """
You are a business strategy consultant helping someone explore investment opportunities.

The user has asked an open-ended advisory question — they do NOT have a specific
product in mind yet. Your job is to give genuinely useful recommendations.

APPROACH:
1. Understand what market/country they're asking about
2. Consider their budget if mentioned
3. Recommend 3-5 specific business opportunities that would work well there
4. For each opportunity: explain WHY it works, what the opportunity size is,
   what competition looks like, and what it takes to succeed
5. Be specific — not "fintech" but "SME working capital lending to small traders"
6. Consider RA Groups' existing strengths (digital lending, fintech, South Asia/GCC)

TONE:
- Conversational and helpful — this is advice, not a formal report
- Be honest about what's hard vs easy
- Prioritise by realistic success probability given context
- If they mentioned a budget, comment on what that budget can realistically achieve

FORMAT: Write in natural, flowing paragraphs. Use headers for each opportunity.
Do NOT write a formal GO/NO_GO report — this is advisory guidance.
"""

async def run_advisory(
    user_query: str,
    market: str,
    budget: float,
    timeline_months: int,
    request_id: str,
) -> str:
    """Generate advisory response for open-ended investment questions."""

    await stream_event(request_id, "agent_start", "advisory_agent",
                       "Researching opportunities…")

    # Pull real market data to ground recommendations
    market_data = {}
    if market and market.lower() not in ("unknown", ""):
        try:
            code    = iso_code(market)
            macro   = get_macro(market)
            lending = get_market_profile(market, "lending")
            nonlend = get_market_profile(market, "non_lending")
            market_data = {
                "market":         market,
                "country_code":   code,
                "gdp_growth":     macro.get("gdp_growth"),
                "inflation":      macro.get("inflation"),
                "lending_rate":   macro.get("lending_rate"),
                "fintech_maturity": macro.get("fintech_maturity"),
                "macro_risk":     macro.get("macro_risk"),
                "lending_market_size":   lending.get("market_size"),
                "lending_growth":        lending.get("annual_growth_pct"),
                "lending_competition":   lending.get("competition"),
                "non_lending_size":      nonlend.get("market_size"),
                "non_lending_growth":    nonlend.get("annual_growth_pct"),
                "non_lending_competition": nonlend.get("competition"),
                "regulatory":            lending.get("regulatory"),
            }
        except Exception:
            pass

    llm = get_reason_llm()

    budget_note = (
        f"Budget: approximately ${budget:,.0f} USD\n"
        if budget > 0
        else "Budget: not specified\n"
    )

    prompt = (
        f"User question: {user_query}\n"
        f"Market/country of interest: {market or 'not specified'}\n"
        f"{budget_note}"
        f"Timeline: {timeline_months} months\n\n"
        f"Market data for {market}:\n{json.dumps(market_data, indent=2)}\n\n"
        "Please provide specific, useful investment recommendations. "
        "Focus on what would realistically work in this market given the budget and context. "
        "Consider RA Groups' strengths in digital lending and fintech."
    )

    resp = await llm.ainvoke([
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=prompt),
    ])

    await stream_event(request_id, "agent_complete", "advisory_agent",
                       {"chars": len(resp.content)})

    return resp.content
