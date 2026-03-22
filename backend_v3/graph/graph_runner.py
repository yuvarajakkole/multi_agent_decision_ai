from graph.decision_graph import build_decision_graph
from streaming.agent_step_streamer import stream_error
from memory.outcome_tracker import save_decision, compute_confidence_adjustment
from core.reliability.confidence import compute_weighted_confidence

_graph=build_decision_graph()

async def run_graph(state: dict) -> dict:
    rid=state.get("request_id","unknown"); market=state.get("market","")
    state["_confidence_adjustment"]=compute_confidence_adjustment(market)
    try:
        result=await _graph.ainvoke(state)
    except Exception as e:
        print(f"Graph error [{rid}]: {e}")
        await stream_error(rid,"graph_runner",str(e)); raise
    envelopes={k:result.get(f"_{k}_envelope",{}) for k in
        ["market_agent","financial_agent","knowledge_agent","strategy_agent"]}
    conf=compute_weighted_confidence(envelopes)
    adj=state.get("_confidence_adjustment",0.0)
    final_conf=round(min(1.0,max(0.0,conf["weighted_confidence"]+adj)),3)
    result["_confidence_report"]=conf; result["_final_confidence"]=final_conf
    strategy=result.get("strategy_decision",{})
    if strategy.get("decision"):
        save_decision(rid,state.get("user_query",""),market,strategy["decision"],
            final_conf,strategy.get("total_score",0),conf.get("per_agent",{}))
    trace=result.get("_trace")
    if trace: result["_decision_trace"]=trace.to_dict()
    return result
