from langgraph.graph import StateGraph
from langgraph.graph.graph import START, END
from schemas.agent_state_schema import AgentState

# supervisor
from supervisor.supervisor_graph import supervisor_node

# agents
from agents.market_agent.graph import market_agent_node
from agents.financial_agent.graph import financial_agent_node
from agents.knowledge_agent.graph import knowledge_agent_node
from agents.strategy_agent.graph import strategy_agent_node
from agents.communication_agent.graph import communication_agent_node


def build_decision_graph():

    builder = StateGraph(AgentState)

    # --------------------------------------------------
    # REGISTER NODES
    # --------------------------------------------------

    builder.add_node("supervisor", supervisor_node)

    builder.add_node("market_agent", market_agent_node)

    builder.add_node("financial_agent", financial_agent_node)

    builder.add_node("knowledge_agent", knowledge_agent_node)

    builder.add_node("strategy_agent", strategy_agent_node)

    builder.add_node("communication_agent", communication_agent_node)

    # --------------------------------------------------
    # GRAPH EDGES
    # --------------------------------------------------

    builder.add_edge(START, "supervisor")

    # builder.add_edge("supervisor", "market_agent")
    # builder.add_edge("supervisor", "financial_agent")
    # builder.add_edge("supervisor", "knowledge_agent")
    builder.add_conditional_edges(
    "supervisor",
    lambda state: state["next_agent"],
    {
        "market_agent": "market_agent",
        "financial_agent": "financial_agent",
        "knowledge_agent": "knowledge_agent",
        "strategy_agent": "strategy_agent",
        "communication_agent": "communication_agent",
    },
)

    builder.add_edge("market_agent", "strategy_agent")
    builder.add_edge("financial_agent", "strategy_agent")
    builder.add_edge("knowledge_agent", "strategy_agent")

    builder.add_edge("strategy_agent", "communication_agent")

    builder.add_edge("communication_agent", END)

    return builder.compile()