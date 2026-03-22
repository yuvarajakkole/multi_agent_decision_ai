"""
graph/graph_runner.py
Runs the full pipeline with:
- Learning loop (past decisions → confidence adjustment)
- System-wide weighted confidence computation
- Decision history persistence
- Trace serialisation for API response
"""
from graph.decision_graph import build_decision_graph
from streaming.agent_step_streamer import stream_error
from memory.outcome_tracker import (
    save_decision, compute_confidence_adjustment,
)
from core.reliability.confidence import compute_weighted_confidence

_graph = build_decision_graph()


async def run_graph(state: dict) -> dict:
    request_id = state.get("request_id", "unknown")
    market     = state.get("market", "")

    # Learning loop: adjust confidence based on past outcomes for this market
    conf_adj = compute_confidence_adjustment(market)
    if conf_adj != 0.0:
        print(f"[Learning] Confidence adjustment for '{market}': {conf_adj:+.3f}")
    state["_confidence_adjustment"] = conf_adj

    try:
        result = await _graph.ainvoke(state)
    except Exception as e:
        print(f"Graph error [{request_id}]: {e}")
        await stream_error(request_id, "graph_runner", str(e))
        raise

    # Compute system-wide weighted confidence
    envelopes = {
        "market_agent":    result.get("_market_agent_envelope",    {}),
        "financial_agent": result.get("_financial_agent_envelope", {}),
        "knowledge_agent": result.get("_knowledge_agent_envelope", {}),
        "strategy_agent":  result.get("_strategy_agent_envelope",  {}),
    }
    conf_report = compute_weighted_confidence(envelopes)

    # Apply learning adjustment to final confidence
    final_conf = round(
        min(1.0, max(0.0, conf_report["weighted_confidence"] + conf_adj)), 3
    )
    result["_confidence_report"] = conf_report
    result["_final_confidence"]  = final_conf

    # Persist decision for future learning
    strategy = result.get("strategy_decision", {})
    if strategy.get("decision"):
        save_decision(
            request_id       = request_id,
            user_query       = state.get("user_query", ""),
            market           = market,
            decision         = strategy["decision"],
            confidence       = final_conf,
            total_score      = strategy.get("total_score", 0),
            agent_confidences= conf_report.get("per_agent", {}),
        )

    # Serialise trace
    trace = result.get("_trace")
    if trace:
        result["_decision_trace"] = trace.to_dict()

    return result
