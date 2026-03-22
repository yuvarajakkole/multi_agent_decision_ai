import json
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from config.llm_config import get_fast_llm
from agents.financial_agent.tools import get_macro_indicators, get_fx_rate, get_market_sentiment

_TOOLS=[get_macro_indicators,get_fx_rate,get_market_sentiment]
_BY_NAME={t.name:t for t in _TOOLS}

_SYSTEM="""
You are a financial analyst. Use ALL tools, then return ONLY this JSON:
{
  "risk_level": "Low|Medium|High|Very High",
  "risk_factors": ["<real factor 1>","<factor 2>","<factor 3>"],
  "currency": "<3-letter code>",
  "exchange_rate_to_usd": <number or null>,
  "currency_stability": "Stable|Moderate|Volatile",
  "inflation_percent": <real number>,
  "gdp_growth_percent": <real number>,
  "lending_rate_percent": <real number>,
  "market_sentiment": "Bullish|Neutral|Bearish",
  "three_month_market_change_pct": <number or null>,
  "macro_environment": "Favorable|Mixed|Challenging",
  "summary": "<2 sentences specific to this market>"
}
risk_level rules — be honest, not balanced:
- High inflation (>10%) → always High or Very High risk
- Negative market sentiment + bearish ETF → always mention both
- Stable currency + low inflation + growing GDP → can be Low or Medium
Output raw JSON only.
"""

async def run_financial_agent(prompt: str) -> str:
    llm=get_fast_llm(); lwt=llm.bind_tools(_TOOLS)
    msgs=[SystemMessage(content=_SYSTEM),HumanMessage(content=prompt)]
    for _ in range(6):
        resp=await lwt.ainvoke(msgs); msgs.append(resp)
        if not resp.tool_calls: return resp.content
        for tc in resp.tool_calls:
            fn=_BY_NAME.get(tc["name"])
            try: result=fn.invoke(tc["args"]) if fn else "Not found"
            except Exception as e: result=f"Error: {e}"
            msgs.append(ToolMessage(
                content=json.dumps(result) if isinstance(result,(dict,list)) else str(result),
                tool_call_id=tc["id"]))
    return (await lwt.ainvoke(msgs)).content
