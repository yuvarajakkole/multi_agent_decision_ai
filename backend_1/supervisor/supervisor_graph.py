# backend/supervisor/supervisor_graph.py

from langgraph.graph import StateGraph
from schemas.agent_state_schema import AgentState
from .supervisor_agent import create_supervisor_agent

from streaming.agent_step_streamer import (
    stream_agent_start,
    stream_agent_complete
)


async def supervisor_node(state):

    print("\n========== SUPERVISOR NODE START ==========")
    print("Input State:", state)

    # Start streaming
    await stream_agent_start(state["request_id"], "supervisor")

    agent = create_supervisor_agent()

    result = await agent.ainvoke({
        "input": state["user_query"]
    })

    print("Supervisor Raw Result:", result)

    plan = result.get("output", "")
    print("Supervisor Plan:", plan)

    # Decide next agent
    if "market" in plan.lower():
        next_agent = "market_agent"
    elif "financial" in plan.lower():
        next_agent = "financial_agent"
    elif "knowledge" in plan.lower():
        next_agent = "knowledge_agent"
    elif "strategy" in plan.lower():
        next_agent = "strategy_agent"
    else:
        next_agent = "communication_agent"

    print("Next Agent Selected:", next_agent)

    state["next_agent"] = next_agent
    state["supervisor_plan"] = plan
    
    if "next_agent" not in state:
        state["next_agent"] = "market_agent"

    print("Updated State:", state)

    # Complete streaming
    await stream_agent_complete(state["request_id"], "supervisor")

    print("========== SUPERVISOR NODE END ==========\n")

    return state


def build_supervisor_graph():

    graph = StateGraph(AgentState)

    graph.add_node("supervisor", supervisor_node)

    graph.set_entry_point("supervisor")
    graph.set_finish_point("supervisor")

    return graph.compile()

# async def supervisor_node(state: AgentState):

#     request_id = state["request_id"]

#     await stream_agent_start(request_id, "supervisor")

#     agent = create_supervisor_agent()

#     query = state["user_query"]

#     result = agent.invoke({
#         "input": query
#     })

#     execution_plan = result["output"]

#     await stream_agent_complete(
#         request_id,
#         "supervisor",
#         {"plan_generated": True}
#     )

#     return {
#         "execution_plan": execution_plan
#     }
