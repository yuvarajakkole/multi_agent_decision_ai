from langgraph.graph import StateGraph

from schemas.agent_state_schema import AgentState

from .agent import create_communication_agent

from streaming.agent_step_streamer import (
    stream_agent_start,
    stream_agent_complete,
    stream_final_result
)


async def communication_agent_node(state: AgentState):

    request_id = state["request_id"]

    await stream_agent_start(request_id, "communication_agent")

    agent = create_communication_agent()

    decision = state.get("strategy_decision", {})
    market = state.get("market_insights", {})
    financial = state.get("financial_analysis", {})
    knowledge = state.get("knowledge_summary", {})

    result = agent.invoke({
        "input": f"""
        Decision: {decision}
        Market: {market}
        Financial: {financial}
        Knowledge: {knowledge}
        """
    })

    report = result["output"]

    await stream_agent_complete(
        request_id,
        "communication_agent",
        {"report_generated": True}
    )

    await stream_final_result(
        request_id,
        decision,
        report
    )

    return {
        "final_report": report
    }


def build_communication_agent_graph():

    graph = StateGraph(AgentState)

    graph.add_node("communication_agent", communication_agent_node)

    graph.set_entry_point("communication_agent")

    graph.set_finish_point("communication_agent")

    return graph.compile()