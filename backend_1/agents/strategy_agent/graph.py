from langgraph.graph import StateGraph

from schemas.agent_state_schema import AgentState

from .agent import create_strategy_agent

from streaming.agent_step_streamer import (
    stream_agent_start,
    stream_agent_complete
)


async def strategy_agent_node(state: AgentState):

    request_id = state["request_id"]

    await stream_agent_start(request_id, "strategy_agent")

    agent = create_strategy_agent()

    market = state.get("market_insights", {})
    financial = state.get("financial_analysis", {})
    knowledge = state.get("knowledge_summary", {})

    result = agent.invoke({
        "input": f"""
        Market: {market}
        Financial: {financial}
        Knowledge: {knowledge}
        """
    })

    decision = {
        "raw_analysis": result["output"]
    }

    await stream_agent_complete(
        request_id,
        "strategy_agent",
        decision
    )

    return {
        "strategy_decision": decision
    }


def build_strategy_agent_graph():

    graph = StateGraph(AgentState)

    graph.add_node("strategy_agent", strategy_agent_node)

    graph.set_entry_point("strategy_agent")

    graph.set_finish_point("strategy_agent")

    return graph.compile()