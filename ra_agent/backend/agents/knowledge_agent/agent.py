"""agents/knowledge_agent/agent.py"""

import json
from typing import Optional
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

from config.llm_config import get_fast_llm
from agents.knowledge_agent.tools import (
    load_company_profile, load_strategic_objectives, load_past_expansions,
    load_financial_health, load_resource_capacity, search_company_context,
)
from agents.knowledge_agent.prompt import SYSTEM, OUTPUT_INSTRUCTIONS, RETRY_INSTRUCTIONS

TOOLS   = [load_company_profile, load_strategic_objectives, load_past_expansions,
           load_financial_health, load_resource_capacity, search_company_context]
BY_NAME = {t.name: t for t in TOOLS}


async def run(
    user_query: str,
    market: str,
    budget: float,
    timeline_months: int,
    previous_output: Optional[str] = None,
    quality_issues:  Optional[list] = None,
) -> str:
    llm = get_fast_llm()
    lwt = llm.bind_tools(TOOLS)

    # Pre-fetch all internal tools and embed data directly in the prompt.
    # This guarantees the LLM sees the actual data and cannot return empty arrays.
    prefetch_lines = []
    for t in [load_company_profile, load_strategic_objectives, load_past_expansions,
              load_financial_health, load_resource_capacity]:
        try:
            result = t.invoke({})
            prefetch_lines.append(f"[{t.name}]:\n{json.dumps(result, indent=1)[:700]}")
        except Exception as e:
            prefetch_lines.append(f"[{t.name}]: error={e}")

    # Also call search tool
    try:
        search_result = search_company_context.invoke({"market": market, "product_type": user_query[:60]})
        prefetch_lines.append(f"[search_company_context]:\n{json.dumps(search_result, indent=1)[:400]}")
    except Exception as e:
        prefetch_lines.append(f"[search_company_context]: error={e}")

    prefetch_block = "\n\n".join(prefetch_lines)

    if previous_output and quality_issues:
        user_content = RETRY_INSTRUCTIONS.format(
            issues=", ".join(quality_issues),
            specific_requests="\n".join(f"- {i}" for i in quality_issues),
            previous_output=previous_output[:600],
        )
    else:
        user_content = (
            f"Query: {user_query}\nMarket: {market}\n"
            f"Budget: ${budget:,.0f}\nTimeline: {timeline_months} months\n\n"
            f"=== INTERNAL DATA (use this in your response) ===\n{prefetch_block}\n\n"
            f"{OUTPUT_INSTRUCTIONS}"
        )

    msgs = [SystemMessage(content=SYSTEM), HumanMessage(content=user_content)]

    for _ in range(10):
        resp = await lwt.ainvoke(msgs)
        msgs.append(resp)
        if not resp.tool_calls:
            return resp.content
        for tc in resp.tool_calls:
            fn = BY_NAME.get(tc["name"])
            try:
                result = fn.invoke(tc["args"]) if fn else f"Unknown tool: {tc['name']}"
            except Exception as e:
                result = {"error": str(e)}
            msgs.append(ToolMessage(
                content=json.dumps(result) if isinstance(result, (dict, list)) else str(result),
                tool_call_id=tc["id"],
            ))

    final = await lwt.ainvoke(msgs)
    return final.content
