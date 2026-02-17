# app/graph.py
# Builds the LangGraph multi-agent pipeline for RA Groups.
from langgraph.graph import StateGraph, START, END
from langchain_core.runnables import RunnableConfig
from .models import DecisionState
from .nodes.market_research import market_research_node
from .nodes.financial_risk import financial_risk_node
from .nodes.knowledge_agent import knowledge_agent_node
from .nodes.strategy_planning import strategy_planning_node
from .nodes.communication import communication_node
def build_decision_graph():
    builder = StateGraph(DecisionState)
    # Nodes (agents)
    builder.add_node("market_research", market_research_node)
    builder.add_node("financial_risk", financial_risk_node)
    builder.add_node("knowledge_agent", knowledge_agent_node)
    builder.add_node("strategy_planning", strategy_planning_node)
    builder.add_node("communication", communication_node)
    # Parallel fan-out from START
    builder.add_edge(START, "market_research")
    builder.add_edge(START, "financial_risk")
    builder.add_edge(START, "knowledge_agent")

    # All converge into strategy planning
    builder.add_edge("market_research", "strategy_planning")
    builder.add_edge("financial_risk", "strategy_planning")
    builder.add_edge("knowledge_agent", "strategy_planning")

    # Then to communication, then END
    builder.add_edge("strategy_planning", "communication")
    builder.add_edge("communication", END)

    return builder.compile()


decision_graph = build_decision_graph()


def run_decision_graph(initial_state: DecisionState) -> DecisionState:
    config = RunnableConfig()
    return decision_graph.invoke(initial_state, config=config)
