import json
from langchain_core.messages import SystemMessage, HumanMessage
from config.llm_config import get_fast_llm
from core.trace.decision_trace import DecisionTrace
from streaming.agent_step_streamer import stream_agent_start, stream_agent_complete

_SYSTEM="""
Analyse the query and return a JSON execution plan.
Always run all 5 agents for expansion/investment/launch queries.

{
  "agents_to_run": ["market_agent","financial_agent","knowledge_agent","strategy_agent","communication_agent"],
  "product_detected": "<exact product from query>",
  "market_detected": "<exact market/country from query>",
  "query_type": "expansion|launch|investment|analysis",
  "reasoning": "<one sentence>"
}
Output raw JSON only.
"""

async def supervisor_node(state: dict) -> dict:
    print("\n========== SUPERVISOR NODE START ==========")
    rid=state["request_id"]; uq=state["user_query"]; market=state.get("market","")
    trace=DecisionTrace(request_id=rid,user_query=uq,market=market)
    trace.start_step("supervisor")
    await stream_agent_start(rid,"supervisor")
    llm=get_fast_llm()
    resp=await llm.ainvoke([SystemMessage(content=_SYSTEM),
        HumanMessage(content=f"Query: {uq}\nMarket: {market}\nBudget: ${state.get('budget',0):,.0f}")])
    raw=resp.content.strip()
    print(f"Supervisor raw: {raw}")
    try:
        plan=json.loads(raw.replace("```json","").replace("```","").strip())
        agents=plan.get("agents_to_run",[]); reasoning=plan.get("reasoning","")
        product=plan.get("product_detected",uq[:50]); mkt=plan.get("market_detected",market)
    except:
        agents=["market_agent","financial_agent","knowledge_agent","strategy_agent","communication_agent"]
        reasoning="Default pipeline"; product=uq[:50]; mkt=market
    trace.log_step("supervisor",{"user_query":uq,"market":market},
        {"agents":agents,"product":product,"market":mkt},1.0,"llm",[],[])
    await stream_agent_complete(rid,"supervisor",{"agents":agents})
    print(f"Plan: {agents}\n========== SUPERVISOR NODE END ==========\n")
    return {"agents_to_run":agents,"next_agent":agents[0] if agents else "market_agent",
        "supervisor_plan":reasoning,"execution_plan":{"agents":agents},"_trace":trace,
        "_detected_product":product,"_detected_market":mkt}
