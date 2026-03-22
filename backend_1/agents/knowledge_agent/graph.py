from langgraph.graph import StateGraph

from schemas.agent_state_schema import AgentState

from .agent import create_knowledge_agent

from streaming.agent_step_streamer import (
    stream_agent_start,
    stream_agent_complete
)


async def knowledge_agent_node(state: AgentState):

    request_id = state["request_id"]

    await stream_agent_start(request_id, "knowledge_agent")

    agent = create_knowledge_agent()

    query = state["user_query"]

    result = agent.invoke({
        "input": query
    })

    summary = {
        "raw_analysis": result["output"]
    }

    await stream_agent_complete(
        request_id,
        "knowledge_agent",
        summary
    )

    return {
        "knowledge_summary": summary
    }


def build_knowledge_agent_graph():

    graph = StateGraph(AgentState)

    graph.add_node("knowledge_agent", knowledge_agent_node)

    graph.set_entry_point("knowledge_agent")

    graph.set_finish_point("knowledge_agent")

    return graph.compile()