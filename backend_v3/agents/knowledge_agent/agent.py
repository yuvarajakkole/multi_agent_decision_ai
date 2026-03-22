import json
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from config.llm_config import get_fast_llm
from agents.knowledge_agent.tools import (
    get_company_profile, get_strategic_objectives, get_all_past_expansions,
    get_financial_history_and_kpis, get_risk_policy_and_budget,
    get_product_portfolio, search_industry_context,
)

_TOOLS=[get_company_profile,get_strategic_objectives,get_all_past_expansions,
        get_financial_history_and_kpis,get_risk_policy_and_budget,
        get_product_portfolio,search_industry_context]
_BY_NAME={t.name:t for t in _TOOLS}

_SYSTEM="""
You are RA Groups' internal strategy analyst. You have direct access to all internal data.

Call ALL tools, then produce this JSON using ONLY tool data:
{
  "company_name": "<from tool>",
  "strategic_fit": "High|Medium|Low",
  "strategic_fit_reasoning": "<specific reason based on core_segments and objectives>",
  "available_budget_usd": <from tool>,
  "budget_within_limits": <true|false>,
  "max_allowed_investment_usd": <from tool>,
  "risk_appetite_match": "Aligned|Partially Aligned|Misaligned",
  "risk_appetite_reasoning": "<explain vs actual risk_appetite from tool>",
  "company_strengths": [
    "<strength from core_segments data>",
    "<strength from past expansion success>",
    "<strength from existing_tech_assets>"
  ],
  "company_weaknesses": [
    "<weakness: e.g. compliance team only N people>",
    "<weakness: e.g. no past expansion in THIS market>",
    "<weakness: e.g. limited to GCC/South Asia focus>"
  ],
  "relevant_past_expansions": [
    {"market":"<from tool>","year":<from tool>,"status":"<from tool>",
     "roi_percent":<from tool>,"npl_percent":<from tool>,"lessons":["<from tool>"]}
  ],
  "has_past_experience_in_this_market": <true|false>,
  "kpi_thresholds": {"min_irr":<from tool>,"min_roi":<from tool>,"max_npl":<from tool>},
  "existing_relevant_products": ["<product name if relevant to query>"],
  "strategic_objectives_alignment": ["<specific alignment point>"],
  "live_industry_context": "<from search tool>",
  "internal_recommendation": "Proceed|Proceed with caution|Do not proceed",
  "internal_recommendation_reason": "<specific reason based on data>",
  "summary": "<2-3 sentences using actual tool data>"
}

RULES:
- company_strengths MUST list items from core_segments or tech_assets — not invented
- relevant_past_expansions MUST list every expansion from get_all_past_expansions
- has_past_experience_in_this_market = true only if the queried market appears in past_expansions
- Output raw JSON. No markdown.
"""

async def run_knowledge_agent(prompt: str) -> str:
    llm=get_fast_llm(); lwt=llm.bind_tools(_TOOLS)
    # Pre-fetch all tools to guarantee data enters context
    prefetch=[]
    market=prompt.split("Market:")[-1].split("\n")[0].strip() if "Market:" in prompt else "general"
    product=prompt.split("Query:")[-1].split("\n")[0].strip()[:80] if "Query:" in prompt else "fintech"
    for t in _TOOLS:
        try:
            args={}
            if t.name=="get_all_past_expansions": args={}
            elif t.name=="search_industry_context": args={"market":market,"product_type":product}
            result=t.invoke(args)
            prefetch.append(f"[{t.name}]:\n{json.dumps(result,indent=1)[:600]}")
        except Exception as e: prefetch.append(f"[{t.name}]: error={e}")
    enriched = prompt+"\n\n=== TOOL DATA (use in your JSON) ===\n"+"\n\n".join(prefetch)+"\n\nOutput JSON now:"
    msgs=[SystemMessage(content=_SYSTEM),HumanMessage(content=enriched)]
    for _ in range(10):
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
