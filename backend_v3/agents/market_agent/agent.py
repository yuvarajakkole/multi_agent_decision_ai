"""
Market Agent — forces product-specific, location-specific analysis.
The prompt is designed so the LLM CANNOT produce a generic answer.
"""
import json
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from config.llm_config import get_fast_llm
from agents.market_agent.tools import (
    get_country_economic_profile, get_world_bank_indicators,
    search_market_news, get_market_size_and_competition,
)

_TOOLS   = [get_country_economic_profile, get_world_bank_indicators,
            search_market_news, get_market_size_and_competition]
_BY_NAME = {t.name:t for t in _TOOLS}

_SYSTEM = """
You are a senior market research analyst. Your analysis MUST be specific to the exact
product and market in the user query — generic answers are unacceptable.

STEP 1 — Call ALL four tools before writing anything:
  get_country_economic_profile(market)
  get_world_bank_indicators(market)
  search_market_news(market, product_type)
  get_market_size_and_competition(market, product_type)

STEP 2 — Using ONLY the tool data, produce this JSON (no extra keys, no markdown):
{
  "market": "<exact country/region from query>",
  "product": "<exact product from query — not a category>",
  "product_category": "<lending|edtech|saas|payments|other>",
  "country_code": "<ISO2 from tool>",
  "population": <from tool>,
  "region": "<from tool>",
  "currency": "<from tool>",
  "gdp_growth_percent": <real number from World Bank or null>,
  "inflation_percent": <real number from World Bank or null>,
  "lending_rate_percent": <real number or null>,
  "gdp_per_capita_usd": <real number or null>,
  "unemployment_percent": <real number or null>,
  "market_size": "<from market_size tool>",
  "annual_growth_pct": <from market_size tool>,
  "market_maturity": "<from market_size tool>",
  "competition_level": "<Low|Medium|High|Very High — from tool, not guessed>",
  "competitor_types": ["<real competitors for THIS product — from tool>"],
  "regulatory_environment": "<Supportive|Moderate|Restrictive — assess from GDP, inflation, lending rate data>",
  "key_regulatory_notes": "<specific to this product category in this country>",
  "market_trends": ["<real trend 1 from search>","<real trend 2>","<real trend 3>"],
  "market_attractiveness_score": <0-100 — YOUR assessment based on tool data>,
  "market_attractiveness": "<one specific sentence — not generic>",
  "go_no_go_signal": "<Strong Go|Cautious Go|Hold|No Go — your recommendation>",
  "key_opportunities": ["<specific opportunity 1>","<specific opportunity 2>"],
  "key_threats": ["<specific threat 1>","<specific threat 2>"],
  "summary": "<3-4 sentences specific to this EXACT product in this EXACT market>"
}

CRITICAL: If GDP growth is high (>5%) AND competition is Low/Medium → market_attractiveness_score should be 65-85.
If GDP growth is negative OR competition is Very High AND market is Mature → score should be 20-45.
The score MUST reflect the actual data — do not default to 50-65 for every query.
"""

async def run_market_agent(prompt: str) -> str:
    llm = get_fast_llm()
    lwt = llm.bind_tools(_TOOLS)
    msgs = [SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)]
    for _ in range(8):
        resp = await lwt.ainvoke(msgs)
        msgs.append(resp)
        if not resp.tool_calls: return resp.content
        for tc in resp.tool_calls:
            fn = _BY_NAME.get(tc["name"])
            try:    result = fn.invoke(tc["args"]) if fn else "Tool not found"
            except Exception as e: result = f"Tool error: {e}"
            msgs.append(ToolMessage(
                content=json.dumps(result) if isinstance(result,(dict,list)) else str(result),
                tool_call_id=tc["id"]))
    final = await lwt.ainvoke(msgs)
    return final.content
