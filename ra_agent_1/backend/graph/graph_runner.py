"""graph/graph_runner.py — Runs the compiled LangGraph and builds response."""

from graph.decision_graph import get_graph
from utils.request_id import new_id
from memory.outcome_tracker import save_decision, confidence_adjustment


async def run(
    user_query: str,
    market: str,
    budget: float = 1_000_000,
    timeline_months: int = 12,
    company_name: str = "RA Groups",
    request_id: str = None,
) -> dict:
    rid = request_id or new_id()

    # Confidence adjustment from learning loop
    adj = confidence_adjustment(market)

    initial_state = {
        "request_id":       rid,
        "user_query":       user_query,
        "market":           market,
        "company_name":     company_name,
        "budget":           float(budget),
        "timeline_months":  int(timeline_months),
        # Initialise counters to 0
        "market_retries":    0,
        "financial_retries": 0,
        "knowledge_retries": 0,
        "strategy_retries":  0,
        "quality_flags":     {},
        "agent_errors":      {},
        "execution_log":     [],
        "_confidence_adj":   adj,
    }

    graph  = get_graph()
    result = await graph.ainvoke(initial_state)

    # Build confidence report
    mc = float(result.get("market_confidence",    0.0))
    fc = float(result.get("financial_confidence", 0.0))
    kc = float(result.get("knowledge_confidence", 0.0))
    sc = float(result.get("strategy_confidence",  0.0))
    wc = round(mc * 0.35 + fc * 0.35 + kc * 0.30, 3)
    wc = min(1.0, max(0.0, wc + adj))

    conf_report = {
        "weighted_confidence": wc,
        "label": "High" if wc >= 0.80 else "Medium" if wc >= 0.60 else "Low",
        "per_agent": {
            "market_agent":    {"confidence": mc},
            "financial_agent": {"confidence": fc},
            "knowledge_agent": {"confidence": kc},
            "strategy_agent":  {"confidence": sc},
        },
        "learning_adjustment": adj,
    }

    # Loop summary (how many retries happened)
    loop_summary = {
        "market_retries":    result.get("market_retries",    0),
        "financial_retries": result.get("financial_retries", 0),
        "knowledge_retries": result.get("knowledge_retries", 0),
        "strategy_retries":  result.get("strategy_retries",  0),
        "total_attempts":    sum([
            result.get("market_retries",    0),
            result.get("financial_retries", 0),
            result.get("knowledge_retries", 0),
            result.get("strategy_retries",  0),
        ]),
    }

    # Save to learning memory
    strategy = result.get("strategy_decision", {})
    if strategy.get("decision"):
        save_decision(
            request_id    = rid,
            user_query    = user_query,
            market        = market,
            decision      = strategy["decision"],
            confidence    = wc,
            score         = strategy.get("adjusted_score", 0),
            agent_confs   = conf_report["per_agent"],
        )

    return {
        "request_id":        rid,
        "decision":          strategy,
        "confidence_report": conf_report,
        "market_insights":   result.get("market_insights",    {}),
        "financial_analysis": result.get("financial_analysis", {}),
        "knowledge_summary": result.get("knowledge_summary",  {}),
        "final_report":      result.get("final_report",       ""),
        "execution_log":     result.get("execution_log",      []),
        "loop_summary":      loop_summary,
        "is_final":          result.get("decision_is_final",  False),
    }
