"""agents/communication_agent/agent.py"""

import json
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from config.llm_config import get_comms_llm
from agents.communication_agent.tools import format_score_table, build_risk_register
from agents.communication_agent.prompt import SYSTEM, REPORT_PROMPT

TOOLS   = [format_score_table, build_risk_register]
BY_NAME = {t.name: t for t in TOOLS}


async def run(
    strategy_decision: dict,
    market_insights:   dict,
    financial_analysis: dict,
    knowledge_summary: dict,
    user_query:        str,
    market:            str,
    budget:            float,
    timeline_months:   int,
) -> str:
    llm = get_comms_llm()
    lwt = llm.bind_tools(TOOLS)

    sd = strategy_decision
    product = market_insights.get("product", user_query[:60])

    content = REPORT_PROMPT.format(
        decision         = sd.get("decision", "WAIT"),
        score            = sd.get("adjusted_score", 0),
        confidence_pct   = sd.get("confidence_pct", 0),
        market           = market,
        product          = product,
        budget           = budget,
        timeline_months  = timeline_months,
        market_summary   = json.dumps({
            k: market_insights.get(k) for k in [
                "gdp_growth_pct", "inflation_pct", "competition_level",
                "market_size", "annual_growth_pct", "go_signal", "summary"
            ]
        }, indent=1),
        financial_summary = json.dumps({
            k: financial_analysis.get(k) for k in [
                "estimated_roi_pct", "estimated_irr_pct", "payback_months",
                "financial_attractiveness", "risk_level", "macro_environment", "summary"
            ]
        }, indent=1),
        knowledge_summary = json.dumps({
            k: knowledge_summary.get(k) for k in [
                "strategic_fit", "has_experience_in_this_market",
                "bandwidth_assessment", "internal_recommendation", "summary"
            ]
        }, indent=1),
        strategy_json = json.dumps({
            k: sd.get(k) for k in [
                "rationale", "key_risks", "conditions",
                "blocking_issues", "next_steps", "score_breakdown"
            ]
        }, indent=1),
    )

    msgs = [SystemMessage(content=SYSTEM), HumanMessage(content=content)]

    for _ in range(6):
        resp = await lwt.ainvoke(msgs)
        msgs.append(resp)
        if not resp.tool_calls:
            return resp.content
        for tc in resp.tool_calls:
            fn = BY_NAME.get(tc["name"])
            try:
                result = fn.invoke(tc["args"]) if fn else f"Unknown tool: {tc['name']}"
            except Exception as e:
                result = f"Tool error: {e}"
            msgs.append(ToolMessage(
                content=str(result),
                tool_call_id=tc["id"],
            ))

    final = await lwt.ainvoke(msgs)
    return final.content
