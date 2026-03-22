"""
Strategy Agent Node — confidence-weighted score adjustment.
Raw LLM score is adjusted based on each upstream agent's data quality.
"""
import json, re
from agents.strategy_agent.agent import run_strategy_agent
from core.reliability.confidence import adjust_decision_score
from core.reliability.validator import validate_agent_output
from core.trace.decision_trace import compact_output
from streaming.agent_step_streamer import stream_agent_start, stream_agent_complete

_FALLBACK_DECISION = {
    "decision": "WAIT", "confidence_score": 40, "total_score": 40,
    "market_component_score": 0, "financial_component_score": 0, "strategic_component_score": 0,
    "rationale": ["Insufficient data for confident decision"],
    "key_risks": ["Data quality issues"], "conditions": [],
    "next_steps": ["Manual review required"],
    "summary": "Automated analysis inconclusive. Manual review recommended.",
}

def _parse(raw: str) -> dict:
    try:
        return json.loads(raw.strip().replace("```json","").replace("```","").strip())
    except Exception:
        pass
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try: return json.loads(m.group())
        except Exception: pass
    return _FALLBACK_DECISION.copy()


async def strategy_agent_node(state: dict) -> dict:
    print("\n========== STRATEGY AGENT NODE START ==========")
    request_id = state["request_id"]
    user_query = state["user_query"]
    market     = state.get("market", "unknown")
    trace      = state.get("_trace")

    # Read upstream envelopes for confidence weighting
    m_conf = state.get("_market_agent_envelope",    {}).get("confidence", 0.7)
    f_conf = state.get("_financial_agent_envelope", {}).get("confidence", 0.7)
    k_conf = state.get("_knowledge_agent_envelope", {}).get("confidence", 0.7)

    if trace: trace.start_step("strategy_agent")
    await stream_agent_start(request_id, "strategy_agent")

    raw      = await run_strategy_agent(
        user_query=user_query, market=market,
        market_insights=state.get("market_insights", {}),
        financial_analysis=state.get("financial_analysis", {}),
        knowledge_summary=state.get("knowledge_summary", {}),
    )
    decision = _parse(raw)

    # Confidence-weighted score adjustment
    raw_score = float(decision.get("total_score", 50))
    adj_score = adjust_decision_score(raw_score, m_conf, f_conf, k_conf)

    # Re-derive decision from adjusted score
    if adj_score >= 75:   final_decision = "GO"
    elif adj_score >= 55: final_decision = "GO_WITH_CONDITIONS"
    elif adj_score >= 35: final_decision = "WAIT"
    else:                 final_decision = "NO_GO"

    decision.update({
        "total_score":          adj_score,
        "raw_score_before_adj": raw_score,
        "decision":             final_decision,
        "agent_confidences": {
            "market_agent":    m_conf,
            "financial_agent": f_conf,
            "knowledge_agent": k_conf,
        },
    })

    # Warn if data quality was low
    low = [n for n, c in [("market",m_conf),("financial",f_conf),("knowledge",k_conf)] if c < 0.6]
    if low:
        decision["rationale"] = decision.get("rationale", []) + [
            f"Note: Low confidence from {', '.join(low)} agents — score adjusted down. Verify data."
        ]

    envelope = validate_agent_output("strategy_agent","strategy_decision", decision, "llm")
    print(f"Strategy: {final_decision} | Score: {adj_score} | Conf: {envelope['confidence']}")

    if trace:
        trace.log_step("strategy_agent",
                       {"market_conf":m_conf,"financial_conf":f_conf,"knowledge_conf":k_conf,"raw_score":raw_score},
                       compact_output(decision),
                       envelope["confidence"], "llm", envelope["errors"], envelope["warnings"])

    await stream_agent_complete(request_id, "strategy_agent",
                                {"decision": final_decision, "score": adj_score,
                                 "confidence": envelope["confidence"]})
    print("========== STRATEGY AGENT NODE END ==========\n")
    return {"strategy_decision": decision, "_strategy_agent_envelope": envelope}
