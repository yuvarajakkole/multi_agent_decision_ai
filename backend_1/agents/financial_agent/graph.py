from langgraph.graph import StateGraph

from schemas.agent_state_schema import AgentState

from .agent import create_financial_agent

from streaming.agent_step_streamer import (
    stream_agent_start,
    stream_agent_complete
)


async def financial_agent_node(state: AgentState):

    request_id = state["request_id"]

    await stream_agent_start(request_id, "financial_agent")

    agent = create_financial_agent()

    budget = state.get("budget", 1000000)

    query = state["user_query"]

    result = agent.invoke({
        "input": f"{query} budget={budget}"
    })

    analysis = {
        "raw_analysis": result["output"]
    }

    await stream_agent_complete(
        request_id,
        "financial_agent",
        analysis
    )

    return {
        "financial_analysis": analysis
    }


def build_financial_agent_graph():

    graph = StateGraph(AgentState)

    graph.add_node("financial_agent", financial_agent_node)

    graph.set_entry_point("financial_agent")

    graph.set_finish_point("financial_agent")

    return graph.compile()