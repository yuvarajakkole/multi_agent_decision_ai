import json
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from config.llm_config import get_communication_llm
from agents.communication_agent.tools import build_summary, build_risk_list, build_recommendations

_TOOLS   = [build_summary, build_risk_list, build_recommendations]
_BY_NAME = {t.name: t for t in _TOOLS}

_SYSTEM = """
You are a senior executive communications specialist.
Convert the structured business analysis into a clear, professional executive report in Markdown.

Use tools to build the summary, risk list, and recommendations — do not fabricate them.

Structure your report:
# Executive Decision Report

## Decision & Confidence
## Executive Summary
## Market Analysis
## Financial Assessment
## Strategic Fit
## Key Risks
## Conditions (if applicable)
## Recommended Next Steps

Write in clear, professional English. Be concise and actionable.
"""


async def run_communication_agent(
    decision: dict, market_insights: dict,
    financial_analysis: dict, knowledge_summary: dict,
) -> str:
    llm = get_communication_llm()
    llm_with_tools = llm.bind_tools(_TOOLS)
    prompt = (
        f"STRATEGY DECISION:\n{json.dumps(decision, indent=2)}\n\n"
        f"MARKET INSIGHTS:\n{json.dumps(market_insights, indent=2)}\n\n"
        f"FINANCIAL ANALYSIS:\n{json.dumps(financial_analysis, indent=2)}\n\n"
        f"KNOWLEDGE SUMMARY:\n{json.dumps(knowledge_summary, indent=2)}\n\n"
        "Use tools. Then write the full executive report."
    )
    msgs = [SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)]

    for _ in range(5):
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
                tool_call_id=tc["id"]))

    final = await llm_with_tools.ainvoke(msgs)
    return final.content
