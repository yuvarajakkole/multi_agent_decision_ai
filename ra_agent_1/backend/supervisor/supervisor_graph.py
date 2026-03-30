"""
supervisor/supervisor_graph.py

The supervisor node runs FIRST and also after quality checks to decide routing.
It does NOT run the agents — it decides which agents run and in what order.

Routing decisions:
  "parallel_research"  → run market + financial + knowledge in parallel
  "retry_market"       → market agent needs to re-run
  "retry_financial"    → financial agent needs to re-run  
  "retry_knowledge"    → knowledge agent needs to re-run
  "strategy"           → all research complete, run strategy agent
  "complete"           → strategy + comms done, end
"""

import json
from datetime import datetime, timezone
from langchain_core.messages import SystemMessage, HumanMessage
from config.llm_config import get_fast_llm
from streaming.streamer import stream_event


_SYSTEM = """
You are an AI orchestration supervisor.
Analyse the query and extract structured information.
Return ONLY this JSON:

{
  "product_detected":   "<exact product/service from query>",
  "market_detected":    "<exact country/region from query>",
  "query_type":         "expansion|launch|investment|analysis|other",
  "budget_mentioned":   <true|false>,
  "timeline_mentioned": <true|false>,
  "complexity":         "simple|moderate|complex",
  "notes":              "<any special considerations>"
}
"""


async def supervisor_node(state: dict) -> dict:
    rid = state["request_id"]
    await stream_event(rid, "agent_start", "supervisor", "Analysing query")
    print(f"\n[supervisor] START  query={state['user_query'][:60]}")

    llm  = get_fast_llm()
    resp = await llm.ainvoke([
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=(
            f"Query: {state['user_query']}\n"
            f"Market: {state.get('market', '')}\n"
            f"Budget: ${state.get('budget', 0):,.0f}\n"
            f"Timeline: {state.get('timeline_months', 12)} months"
        )),
    ])

    plan = {}
    try:
        cleaned = resp.content.strip().replace("```json", "").replace("```", "").strip()
        plan    = json.loads(cleaned)
    except Exception:
        plan = {
            "product_detected": state["user_query"][:50],
            "market_detected":  state.get("market", ""),
            "query_type":       "analysis",
        }

    print(f"[supervisor] plan={plan}")

    await stream_event(rid, "agent_complete", "supervisor", {
        "product": plan.get("product_detected"),
        "market":  plan.get("market_detected"),
        "type":    plan.get("query_type"),
    })

    return {
        "supervisor_plan":  plan,
        "routing_decision": "parallel_research",
        "_detected_product": plan.get("product_detected", state["user_query"][:50]),
        "execution_log": [{
            "agent":     "supervisor",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action":    "query_analysed",
            "plan":      plan,
        }],
    }
