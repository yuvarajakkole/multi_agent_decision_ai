"""
Market Agent — tool-first, LLM only interprets tool outputs.
"""
import json
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from config.llm_config import get_fast_llm
from agents.market_agent.tools import (
    get_country_profile, get_world_bank_macro,
    get_competitor_landscape, estimate_market_size,
)

_TOOLS = [get_country_profile, get_world_bank_macro,
          get_competitor_landscape, estimate_market_size]
_BY_NAME = {t.name: t for t in _TOOLS}

_SYSTEM = """
You are a senior fintech market research analyst.
You MUST call ALL available tools to fetch real market data before writing your analysis.
Never fabricate data — only interpret what the tools return.

After using tools, return ONLY a JSON object with these keys:
market, product, country_code, population, region, currency,
gdp_growth_percent, inflation_percent, lending_rate_percent,
market_size_usd, growth_rate_pct, competition_level, competitor_types,
regulatory_environment, key_regulatory_notes, market_trends,
market_attractiveness, summary.

Output raw JSON only. No markdown fences.
"""


async def run_market_agent(prompt: str) -> str:
    llm  = get_fast_llm()
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
            msgs.append(ToolMessage(content=json.dumps(result) if isinstance(result, dict) else str(result),
                                    tool_call_id=tc["id"]))

    final = await llm_with_tools.ainvoke(msgs)
    return final.content
