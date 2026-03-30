"""
agents/market_agent/agent.py

Main agent logic.  Uses LangChain's bind_tools ReAct pattern so the LLM can
call tools in a loop until it has enough data, then produces structured output.
"""

import json
from typing import Optional
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

from config.llm_config import get_fast_llm
from agents.market_agent.tools import (
    get_country_profile,
    get_world_bank_data,
    get_market_size,
    search_market_news,
)
from agents.market_agent.prompt import SYSTEM, ANALYSIS_INSTRUCTIONS, RETRY_INSTRUCTIONS

TOOLS    = [get_country_profile, get_world_bank_data, get_market_size, search_market_news]
BY_NAME  = {t.name: t for t in TOOLS}
MAX_ITER = 10   # max tool-call iterations before forcing an answer


async def run(
    user_query: str,
    market: str,
    budget: float,
    timeline_months: int,
    previous_output: Optional[str] = None,
    quality_issues: Optional[list] = None,
) -> str:
    """
    Execute the market agent.
    Returns raw LLM output (JSON string).

    If previous_output + quality_issues are provided, this is a retry loop —
    the agent is told what was wrong and asked to correct it.
    """
    llm  = get_fast_llm()
    llm_with_tools = llm.bind_tools(TOOLS)

    # Build human message
    if previous_output and quality_issues:
        # ── Retry path ────────────────────────────────────────────────────
        user_content = RETRY_INSTRUCTIONS.format(
            issues=", ".join(quality_issues),
            specific_requests="\n".join(f"- {i}" for i in quality_issues),
            previous_output=previous_output[:800],
        )
    else:
        # ── First-run path ────────────────────────────────────────────────
        user_content = (
            f"Analyse the following query. Every field in your output must be specific "
            f"to this exact product and this exact market — not generic.\n\n"
            f"Query:           {user_query}\n"
            f"Target Market:   {market}\n"
            f"Budget:          ${budget:,.0f}\n"
            f"Timeline:        {timeline_months} months\n\n"
            f"{ANALYSIS_INSTRUCTIONS}"
        )

    msgs = [
        SystemMessage(content=SYSTEM),
        HumanMessage(content=user_content),
    ]

    for _iteration in range(MAX_ITER):
        response = await llm_with_tools.ainvoke(msgs)
        msgs.append(response)

        # No tool calls → LLM produced its final answer
        if not response.tool_calls:
            return response.content

        # Execute all tool calls
        for tc in response.tool_calls:
            fn = BY_NAME.get(tc["name"])
            try:
                result = fn.invoke(tc["args"]) if fn else f"Unknown tool: {tc['name']}"
            except Exception as e:
                result = {"error": str(e), "tool": tc["name"]}

            msgs.append(ToolMessage(
                content=json.dumps(result) if isinstance(result, (dict, list)) else str(result),
                tool_call_id=tc["id"],
            ))

    # Force answer after max iterations
    final = await llm_with_tools.ainvoke(msgs)
    return final.content
