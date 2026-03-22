"""
Communication Agent Node — generates the final markdown executive report.
"""
from agents.communication_agent.agent import run_communication_agent
from core.trace.decision_trace import compact_input
from streaming.agent_step_streamer import (
    stream_agent_start, stream_agent_complete, stream_final_result,
)


async def communication_agent_node(state: dict) -> dict:
    print("\n========== COMMUNICATION AGENT NODE START ==========")
    request_id = state["request_id"]
    decision   = state.get("strategy_decision", {})
    trace      = state.get("_trace")

    if trace: trace.start_step("communication_agent")
    await stream_agent_start(request_id, "communication_agent")

    report = await run_communication_agent(
        decision=decision,
        market_insights=state.get("market_insights", {}),
        financial_analysis=state.get("financial_analysis", {}),
        knowledge_summary=state.get("knowledge_summary", {}),
    )

    if trace:
        trace.log_step(
            "communication_agent",
            compact_input(state),
            {"report_length_chars": len(report), "decision": decision.get("decision")},
            confidence=1.0, source="llm", errors=[], warnings=[],
        )

    await stream_agent_complete(request_id, "communication_agent",
                                {"report_generated": True, "chars": len(report)})
    await stream_final_result(request_id, decision, report)

    print("========== COMMUNICATION AGENT NODE END ==========\n")
    return {"final_report": report}
