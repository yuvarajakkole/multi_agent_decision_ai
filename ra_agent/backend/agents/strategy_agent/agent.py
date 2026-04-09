"""agents/strategy_agent/agent.py

Updated to accept ignored_agents list — prompt tells LLM which agents to skip.
Budget=0 is now passed as-is (not defaulted) and surfaced in prompt.
"""

import json
from typing import Optional
from langchain_core.messages import SystemMessage, HumanMessage
from config.llm_config import get_reason_llm
from agents.strategy_agent.prompt import SYSTEM, ANALYSIS_PROMPT, RETRY_PROMPT


async def run(
    user_query: str,
    market: str,
    budget: float,
    timeline_months: int,
    market_insights: dict,
    financial_analysis: dict,
    knowledge_summary: dict,
    market_confidence: float,
    financial_confidence: float,
    knowledge_confidence: float,
    ignored_agents: list = None,
    quality_flags: dict = None,
    previous_decision: Optional[str] = None,
    retry_issues: Optional[list] = None,
) -> str:
    llm = get_reason_llm()

    ignored = ignored_agents or []
    ignored_note = (
        f"\n⚠ IGNORED AGENTS (confidence < threshold — do NOT use their data): {ignored}"
        if ignored else ""
    )

    budget_note = (
        f"${budget:,.0f}" if budget > 0
        else "NOT SPECIFIED — financial calculations may be unreliable"
    )

    if previous_decision and retry_issues:
        content = RETRY_PROMPT.format(
            previous_decision=previous_decision,
            issues="\n".join(f"- {i}" for i in retry_issues),
        )
    else:
        content = ANALYSIS_PROMPT.format(
            user_query           = user_query,
            market               = market,
            budget               = budget_note,
            timeline_months      = timeline_months,
            market_confidence    = market_confidence,
            financial_confidence = financial_confidence,
            knowledge_confidence = knowledge_confidence,
            ignored_note         = ignored_note,
            market_data          = json.dumps(market_insights,    indent=2),
            financial_data       = json.dumps(financial_analysis, indent=2),
            knowledge_data       = json.dumps(knowledge_summary,  indent=2),
            quality_flags        = json.dumps(quality_flags or {}, indent=2),
        )

    resp = await llm.ainvoke([
        SystemMessage(content=SYSTEM),
        HumanMessage(content=content),
    ])
    return resp.content
