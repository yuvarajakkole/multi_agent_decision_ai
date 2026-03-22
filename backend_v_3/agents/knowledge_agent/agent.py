import json
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from config.llm_config import get_fast_llm
from agents.knowledge_agent.tools import (
    get_company_profile, get_strategic_objectives,
    get_past_expansions, get_financial_history,
    get_risk_policies_and_budget, search_industry_context,
)

_TOOLS   = [get_company_profile, get_strategic_objectives,
            get_past_expansions, get_financial_history,
            get_risk_policies_and_budget, search_industry_context]
_BY_NAME = {t.name: t for t in _TOOLS}

_SYSTEM = """
You are a corporate strategy analyst with full access to RA Groups internal data.
Call ALL tools before writing your analysis.

Return ONLY a JSON object with:
company_name, strategic_fit, available_budget_usd, budget_within_limits,
max_allowed_investment_usd, risk_appetite_match, company_strengths (list),
company_weaknesses (list), relevant_past_expansions (list),
strategic_objectives_alignment (list), live_industry_context,
recommendation_from_knowledge, summary.

strategic_fit must be "High" | "Medium" | "Low".
budget_within_limits must be true | false.
Output raw JSON only. No markdown.
"""


async def run_knowledge_agent(prompt: str) -> str:
    llm = get_fast_llm()
    llm_with_tools = llm.bind_tools(_TOOLS)
    msgs = [SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)]

    for _ in range(7):
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
