from langgraph.graph import StateGraph

from schemas.agent_state_schema import AgentState

from .agent import create_market_agent
from streaming.agent_step_streamer import (
    stream_agent_start,
    stream_agent_complete
)


async def market_agent_node(state: AgentState):

    request_id = state["request_id"]

    await stream_agent_start(request_id, "market_agent")

    agent = create_market_agent()

    query = state["user_query"]
    market = state["market"]

    result = agent.invoke({
        "input": f"{query} market={market}"
    })

    insights = {
        "raw_analysis": result["output"]
    }

    await stream_agent_complete(
        request_id,
        "market_agent",
        insights
    )

    return {
        "market_insights": insights
    }


def build_market_agent_graph():

    graph = StateGraph(AgentState)

    graph.add_node("market_agent", market_agent_node)

    graph.set_entry_point("market_agent")

    graph.set_finish_point("market_agent")

    return graph.compile()