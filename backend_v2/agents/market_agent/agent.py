"""
Market Agent — tool-first, LLM interprets real data.
Product-aware: competitor types and market analysis adapt to what's being evaluated.
"""
import json
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from config.llm_config import get_fast_llm
from agents.market_agent.tools import (
    get_country_profile,
    get_world_bank_macro,
    get_competitor_landscape,
    estimate_market_size,
)

_TOOLS   = [get_country_profile, get_world_bank_macro, get_competitor_landscape, estimate_market_size]
_BY_NAME = {t.name: t for t in _TOOLS}

_SYSTEM = """
You are a senior market research analyst. You MUST call ALL tools before writing any analysis.

After collecting tool data, return ONLY a JSON object with these keys:
{
  "market": "<country or market name>",
  "product": "<specific product being evaluated — from the user query>",
  "country_code": "<ISO 2-letter code>",
  "population": <number>,
  "region": "<from tool>",
  "currency": "<from tool>",
  "gdp_growth_percent": <from World Bank tool>,
  "inflation_percent": <from World Bank tool>,
  "lending_rate_percent": <from World Bank tool>,
  "market_size_usd": "<estimated market size for THIS SPECIFIC PRODUCT — not generic fintech>",
  "growth_rate_pct": <annual growth rate for THIS SPECIFIC PRODUCT SEGMENT>,
  "competition_level": "Low|Medium|High",
  "competitor_types": [
    "<real competitors for THIS SPECIFIC PRODUCT — NOT generic fintech lists>",
    "<e.g. for EdTech: local edtech startups, BYJU's, Unacademy, Google Classroom>",
    "<e.g. for SME lending: local banks, NBFCs, fintech lenders>"
  ],
  "regulatory_environment": "Supportive|Moderate|Restrictive",
  "key_regulatory_notes": "<specific regulations relevant to THIS product in THIS market>",
  "market_trends": "<2-3 real trends specific to THIS product type in THIS market>",
  "market_attractiveness": "<one sentence assessment — specific to this product/market combo>",
  "summary": "<3-4 sentence analysis specific to THIS product in THIS market>"
}

CRITICAL:
- competitor_types MUST reflect the actual product being evaluated (not a generic fintech list)
- market_size_usd MUST be for the specific product segment (EdTech, AI, SME lending, etc.)
- If product is NOT fintech lending, do NOT list banks and neobanks as competitors
- Output raw JSON only. No markdown fences.
"""


async def run_market_agent(prompt: str) -> str:
    llm            = get_fast_llm()
    llm_with_tools = llm.bind_tools(_TOOLS)
    msgs = [SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)]

    for _ in range(6):
        resp = await llm_with_tools.ainvoke(msgs)
        msgs.append(resp)
        if not resp.tool_calls:
            return resp.content
        for tc in resp.tool_calls:
            fn = _BY_NAME.get(tc["name"])
            try:
                result = fn.invoke(tc["args"]) if fn else "Tool not found"
            except Exception as e:
                result = f"Tool error: {e}"
            msgs.append(ToolMessage(
                content=json.dumps(result) if isinstance(result, (dict, list)) else str(result),
                tool_call_id=tc["id"],
            ))

    final = await llm_with_tools.ainvoke(msgs)
    return final.content
