from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from config.llm_config import get_fast_llm
from agents.financial_agent.tools import (
    get_real_macro_indicators,
    get_currency_exchange_rate,
    get_stock_market_data,
    calculate_roi_projection,
    get_fintech_market_etf,
)
from agents.financial_agent.prompt import FINANCIAL_SYSTEM_PROMPT

_tools = [
    get_real_macro_indicators,
    get_currency_exchange_rate,
    get_stock_market_data,
    calculate_roi_projection,
    get_fintech_market_etf,
]
_tools_by_name = {t.name: t for t in _tools}


async def run_financial_agent(user_input: str) -> str:
    llm = get_fast_llm()
    llm_with_tools = llm.bind_tools(_tools)

    messages = [
        SystemMessage(content=FINANCIAL_SYSTEM_PROMPT),
        HumanMessage(content=user_input),
    ]

    for _ in range(5):
        response = await llm_with_tools.ainvoke(messages)
        messages.append(response)

        if not response.tool_calls:
            return response.content

        for tool_call in response.tool_calls:
            tool_fn = _tools_by_name.get(tool_call["name"])
            try:
                result = tool_fn.invoke(tool_call["args"]) if tool_fn else f"Unknown tool: {tool_call['name']}"
            except Exception as e:
                result = f"Tool error: {e}"
            messages.append(
                ToolMessage(content=str(result), tool_call_id=tool_call["id"])
            )

    messages.append(HumanMessage(content="Return your final JSON answer now."))
    final = await llm_with_tools.ainvoke(messages)
    return final.content