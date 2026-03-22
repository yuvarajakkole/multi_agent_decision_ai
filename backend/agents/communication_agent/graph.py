from agents.communication_agent.agent import run_communication_agent
from streaming.agent_step_streamer import (
    stream_agent_start,
    stream_agent_complete,
    stream_final_result,
)


# ---------------------------------------------------------
# COMMUNICATION AGENT NODE
# FIX: Was calling agent.invoke() (sync) inside async def.
#      Now uses run_communication_agent which calls ainvoke.
# This is the final node — streams the complete result to UI.
# ---------------------------------------------------------

async def communication_agent_node(state: dict) -> dict:

    print("\n========== COMMUNICATION AGENT NODE START ==========")

    request_id = state["request_id"]
    user_query = state["user_query"]
    market     = state.get("market", "unknown market")

    strategy_decision  = state.get("strategy_decision", {})
    market_insights    = state.get("market_insights", {})
    financial_analysis = state.get("financial_analysis", {})
    knowledge_summary  = state.get("knowledge_summary", {})

    await stream_agent_start(request_id, "communication_agent")

    final_report = await run_communication_agent(
        user_query=user_query,
        market=market,
        strategy_decision=strategy_decision,
        market_insights=market_insights,
        financial_analysis=financial_analysis,
        knowledge_summary=knowledge_summary,
    )

    print(f"Communication agent report length: {len(final_report)} chars")

    await stream_agent_complete(
        request_id,
        "communication_agent",
        {"report_generated": True, "report_length": len(final_report)}
    )

    # Stream the complete final result to the frontend
    await stream_final_result(
        request_id=request_id,
        decision=strategy_decision,
        final_report=final_report,
    )

    print("========== COMMUNICATION AGENT NODE END ==========\n")

    return {"final_report": final_report}
