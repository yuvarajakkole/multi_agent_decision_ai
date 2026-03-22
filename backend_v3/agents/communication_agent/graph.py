from agents.communication_agent.agent import run_communication_agent
from core.trace.decision_trace import compact_input
from streaming.agent_step_streamer import stream_agent_start, stream_agent_complete, stream_final_result

async def communication_agent_node(state: dict) -> dict:
    print("\n========== COMMUNICATION AGENT NODE START ==========")
    rid=state["request_id"]; decision=state.get("strategy_decision",{}); trace=state.get("_trace")
    if trace: trace.start_step("communication_agent")
    await stream_agent_start(rid,"communication_agent")
    report=await run_communication_agent(decision,
        state.get("market_insights",{}),state.get("financial_analysis",{}),state.get("knowledge_summary",{}))
    if trace: trace.log_step("communication_agent",compact_input(state),
        {"chars":len(report),"decision":decision.get("decision")},
        1.0,"llm",[],[])
    await stream_agent_complete(rid,"communication_agent",{"chars":len(report)})
    await stream_final_result(rid,decision,report)
    print("========== COMMUNICATION AGENT NODE END ==========\n")
    return {"final_report":report}
