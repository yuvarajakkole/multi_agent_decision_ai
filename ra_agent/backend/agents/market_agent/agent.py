"""
agents/market_agent/agent.py

ReAct agent using LangChain bind_tools.
CRITICAL CHANGE: we now intercept tool results and track the BEST confidence
seen from live tools, so graph.py doesn't have to guess from LLM output.
Returns (raw_str, tool_confidence, tool_source) instead of just raw_str.
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

TOOLS   = [get_country_profile, get_world_bank_data, get_market_size, search_market_news]
BY_NAME = {t.name: t for t in TOOLS}
MAX_ITER = 12


async def run(
    user_query:      str,
    market:          str,
    budget:          float,
    timeline_months: int,
    previous_output: Optional[str] = None,
    quality_issues:  Optional[list] = None,
) -> tuple[str, float, str]:
    """
    Returns:
        raw_str        – LLM JSON output string
        tool_conf      – best confidence seen from live tools (not LLM guess)
        tool_source    – source label from best tool result
    """
    llm            = get_fast_llm()
    llm_with_tools = llm.bind_tools(TOOLS)

    # Track best data source quality seen across all tool calls
    best_tool_conf   = 0.0
    best_tool_source = "static"

    if previous_output and quality_issues:
        user_content = RETRY_INSTRUCTIONS.format(
            issues           = ", ".join(quality_issues),
            specific_requests= "\n".join(f"- {i}" for i in quality_issues),
            previous_output  = previous_output[:800],
        )
    else:
        user_content = (
            f"Analyse the following query. Every field must be specific to this exact "
            f"product and market — not generic.\n\n"
            f"Query:          {user_query}\n"
            f"Target Market:  {market}\n"
            f"Budget:         ${budget:,.0f}\n"
            f"Timeline:       {timeline_months} months\n\n"
            f"{ANALYSIS_INSTRUCTIONS}"
        )

    msgs = [
        SystemMessage(content=SYSTEM),
        HumanMessage(content=user_content),
    ]

    for _iteration in range(MAX_ITER):
        response = await llm_with_tools.ainvoke(msgs)
        msgs.append(response)

        if not response.tool_calls:
            # LLM produced final answer
            return response.content, best_tool_conf, best_tool_source

        for tc in response.tool_calls:
            fn = BY_NAME.get(tc["name"])
            try:
                result = fn.invoke(tc["args"]) if fn else {"error": f"Unknown tool: {tc['name']}"}
            except Exception as e:
                result = {"error": str(e), "tool": tc["name"]}

            # Track best tool confidence DIRECTLY from tool output (not from LLM guess)
            if isinstance(result, dict):
                t_conf   = float(result.get("confidence", 0.0) or 0.0)
                t_source = str(result.get("source", "static"))
                t_ignore = bool(result.get("ignore", True))

                # Only update if this tool gives better confidence and is not ignored
                if not t_ignore and t_conf > best_tool_conf:
                    best_tool_conf   = t_conf
                    best_tool_source = t_source

            msgs.append(ToolMessage(
                content      = json.dumps(result) if isinstance(result, (dict, list)) else str(result),
                tool_call_id = tc["id"],
            ))

    # Exhausted iterations — force final answer
    final = await llm_with_tools.ainvoke(msgs)
    return final.content, best_tool_conf, best_tool_source
