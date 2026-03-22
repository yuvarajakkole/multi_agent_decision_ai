from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from config.llm_config import get_fast_llm
from agents.knowledge_agent.tools import (
    get_company_profile,
    get_strategic_objectives,
    get_past_expansions,
    get_financial_history,
    get_risk_policies_and_budget,
    search_industry_context,
)
from agents.knowledge_agent.prompt import KNOWLEDGE_SYSTEM_PROMPT

_tools = [
    get_company_profile,
    get_strategic_objectives,
    get_past_expansions,
    get_financial_history,
    get_risk_policies_and_budget,
    search_industry_context,
]
_tools_by_name = {t.name: t for t in _tools}


async def run_knowledge_agent(user_input: str) -> str:
    llm = get_fast_llm()
    llm_with_tools = llm.bind_tools(_tools)

    messages = [
        SystemMessage(content=KNOWLEDGE_SYSTEM_PROMPT),
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