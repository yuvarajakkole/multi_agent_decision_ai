import json
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from config.llm_config import get_communication_llm
from agents.communication_agent.tools import format_decision_headline, build_risk_register

_TOOLS=[format_decision_headline,build_risk_register]
_BY_NAME={t.name:t for t in _TOOLS}

_SYSTEM="""
You are RA Groups' executive communication specialist.
Write a precise, honest executive decision report in Markdown.
The report must reflect the ACTUAL scores and data — no sugar-coating a NO_GO,
no downplaying a GO. Cite real numbers throughout.

Structure:
# RA Groups — Executive Decision Report
## [Use format_decision_headline tool for the title line]
## Score Breakdown
  Table: Market Score | Financial Score | Strategic Score | Total | Decision
## Executive Summary (2 paragraphs — cite actual scores and key data points)
## Market Analysis (specific to the queried product+market, use real GDP/inflation numbers)
## Financial Assessment (cite ROI %, IRR %, payback period in months)
## Strategic Fit Assessment (cite strengths, weaknesses, past experience)
## Risk Register (use build_risk_register tool)
## Conditions & Requirements (only if GO_WITH_CONDITIONS — be specific)
## Recommended Next Steps (actionable, prioritised)
---
*Confidence: [weighted_confidence]% | Generated: [timestamp]*
"""

async def run_communication_agent(decision, market_insights, financial_analysis, knowledge_summary) -> str:
    llm=get_communication_llm(); lwt=llm.bind_tools(_TOOLS)
    prompt=(f"DECISION:\n{json.dumps(decision,indent=2)}\n\n"
        f"MARKET:\n{json.dumps(market_insights,indent=2)}\n\n"
        f"FINANCIAL:\n{json.dumps(financial_analysis,indent=2)}\n\n"
        f"KNOWLEDGE:\n{json.dumps(knowledge_summary,indent=2)}\n\n"
        "Use tools, then write the complete executive report in Markdown.")
    msgs=[SystemMessage(content=_SYSTEM),HumanMessage(content=prompt)]
    for _ in range(5):
        resp=await lwt.ainvoke(msgs); msgs.append(resp)
        if not resp.tool_calls: return resp.content
        for tc in resp.tool_calls:
            fn=_BY_NAME.get(tc["name"])
            try: result=fn.invoke(tc["args"]) if fn else "Not found"
            except Exception as e: result=f"Error:{e}"
            msgs.append(ToolMessage(
                content=json.dumps(result) if isinstance(result,(dict,list)) else str(result),
                tool_call_id=tc["id"]))
    return (await lwt.ainvoke(msgs)).content
