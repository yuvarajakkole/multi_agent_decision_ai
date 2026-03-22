"""
Knowledge Agent — tool-first with explicit tool-call enforcement.
The LLM MUST use real tool data — it cannot populate strengths/weaknesses from imagination.
"""
import json
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from config.llm_config import get_fast_llm
from agents.knowledge_agent.tools import (
    get_company_profile,
    get_strategic_objectives,
    get_past_expansions,
    get_financial_history,
    get_risk_policies_and_budget,
    get_product_portfolio,
    search_industry_context,
)

_TOOLS   = [
    get_company_profile,
    get_strategic_objectives,
    get_past_expansions,
    get_financial_history,
    get_risk_policies_and_budget,
    get_product_portfolio,
    search_industry_context,
]
_BY_NAME = {t.name: t for t in _TOOLS}

_SYSTEM = """
You are a corporate strategy analyst with FULL ACCESS to RA Groups internal data via tools.

MANDATORY STEP 1 — call ALL tools before writing ANYTHING:
  get_company_profile        → company name, core segments, headquarters
  get_strategic_objectives   → 3-year goals, risk appetite, priority themes
  get_past_expansions        → all past market expansions and lessons
  get_financial_history      → revenue, EBIT margin, KPI benchmarks
  get_risk_policies_and_budget → budget limits, credit risk guidelines
  get_product_portfolio      → existing products and their performance
  search_industry_context    → live industry news for the target market

MANDATORY STEP 2 — after ALL tools have returned, synthesise ONLY their data into this JSON:
{
  "company_name": "<from tool>",
  "strategic_fit": "High|Medium|Low",
  "available_budget_usd": <number from get_risk_policies_and_budget>,
  "budget_within_limits": <true|false — budget_requested <= max_single_market_usd>,
  "max_allowed_investment_usd": <from tool>,
  "risk_appetite_match": "Aligned|Partially Aligned|Misaligned",
  "company_strengths": [
    "<list from core_segments, past expansion successes, tech_assets — MUST NOT be empty>",
    "<e.g. 'Strong retail lending capabilities from core_segments'>",
    "<e.g. 'Proven AI-based credit scoring from tech_assets'>"
  ],
  "company_weaknesses": [
    "<identify real weaknesses from the data — e.g. small compliance team, limited markets>",
    "<check compliance_team_size, past expansion NPL rates, concentration limits>"
  ],
  "relevant_past_expansions": [
    {
      "market": "<from tool>",
      "year": <from tool>,
      "outcome": "<from tool>",
      "roi_percent": <from tool>,
      "key_lessons": ["<from tool>", "..."]
    }
  ],
  "strategic_objectives_alignment": [
    "<how THIS specific query aligns with the 3-year objectives — from tool data>"
  ],
  "product_portfolio_fit": [
    "<which existing products are relevant to this query — from get_product_portfolio>"
  ],
  "live_industry_context": "<from search_industry_context tool>",
  "recommendation_from_knowledge": "<one paragraph — base on real tool data>",
  "summary": "<one paragraph summary>"
}

CRITICAL RULES:
- company_strengths MUST contain at least 3 items derived from tool data
- relevant_past_expansions MUST list all expansions returned by get_past_expansions
- If get_past_expansions returns empty, explicitly say "No past expansions found in dataset"
- Output raw JSON only — no markdown fences, no extra text
"""


async def run_knowledge_agent(prompt: str) -> str:
    llm            = get_fast_llm()
    llm_with_tools = llm.bind_tools(_TOOLS)

    # Pre-load all tool data ourselves to guarantee it enters context
    # (Some LLMs skip tools even when instructed — this ensures data is always present)
    prefetch_msgs = []
    for tool in _TOOLS:
        try:
            # Call with sensible defaults; graph prompt contains the real query
            args = {}
            if tool.name == "get_past_expansions":
                args = {"market": ""}
            elif tool.name == "search_industry_context":
                # extract market from prompt
                market = prompt.split("Market:")[-1].split("\n")[0].strip() if "Market:" in prompt else "general"
                product = prompt.split("Query:")[-1].split("\n")[0].strip()[:50] if "Query:" in prompt else "fintech"
                args = {"market": market, "product_type": product}
            result = tool.invoke(args)
            prefetch_msgs.append(f"[{tool.name} result]: {json.dumps(result)[:800]}")
        except Exception as e:
            prefetch_msgs.append(f"[{tool.name} error]: {e}")

    # Build enriched prompt with pre-fetched data embedded
    enriched_prompt = (
        prompt + "\n\n"
        "=== PRE-LOADED TOOL DATA (use this data in your JSON output) ===\n"
        + "\n".join(prefetch_msgs)
        + "\n\nNow output the JSON using ONLY the above tool data."
    )

    msgs = [SystemMessage(content=_SYSTEM), HumanMessage(content=enriched_prompt)]

    # Also allow tool calls in case LLM wants to dig deeper
    for _ in range(10):
        resp = await llm_with_tools.ainvoke(msgs)
        msgs.append(resp)
        if not resp.tool_calls:
            return resp.content
        for tc in resp.tool_calls:
            fn = _BY_NAME.get(tc["name"])
            try:
                result = fn.invoke(tc["args"]) if fn else f"Tool '{tc['name']}' not found"
            except Exception as e:
                result = f"Tool error: {e}"
            msgs.append(ToolMessage(
                content=json.dumps(result) if isinstance(result, (dict, list)) else str(result),
                tool_call_id=tc["id"],
            ))

    final = await llm_with_tools.ainvoke(msgs)
    return final.content
