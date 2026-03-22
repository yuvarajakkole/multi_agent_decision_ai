"""
Financial Agent — tool-first. LLM only interprets qualitative context.
All numeric metrics (ROI, IRR, payback) computed in graph.py by financial.py.
"""
import json
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from config.llm_config import get_fast_llm
from agents.financial_agent.tools import (
    get_real_macro_indicators, get_currency_exchange_rate,
    get_stock_market_index, get_fintech_etf_performance,
)

_TOOLS   = [get_real_macro_indicators, get_currency_exchange_rate,
            get_stock_market_index, get_fintech_etf_performance]
_BY_NAME = {t.name: t for t in _TOOLS}

_SYSTEM = """
You are a senior financial analyst. You MUST call all available tools to gather
real data before writing your analysis. Do NOT compute ROI or IRR yourself.

After collecting tool data, return ONLY a JSON object with:
currency, exchange_rate_to_usd, currency_stability,
inflation_percent, gdp_growth_percent, lending_rate_percent,
stock_index_performance, fintech_etf_sentiment, risk_level,
risk_factors (list), macro_environment_summary, summary.

risk_level must be "Low" | "Medium" | "High".
Output raw JSON only. No markdown.
"""


async def run_financial_agent(prompt: str) -> str:
    llm = get_fast_llm()
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
                content=json.dumps(result) if isinstance(result, dict) else str(result),
                tool_call_id=tc["id"]))

    final = await llm_with_tools.ainvoke(msgs)
    return final.content
