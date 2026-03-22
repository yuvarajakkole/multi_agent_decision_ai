"""
graph/decision_graph.py
Parallel fan-out: market, financial, knowledge run concurrently.
Strategy and communication run sequentially after all three complete.

Flow:
  START → supervisor → [market || financial || knowledge] → strategy → communication → END
"""
from langgraph.graph import StateGraph

try:
    from langgraph.graph import START, END
except ImportError:
    try:
        from langgraph.constants import START, END
    except ImportError:
        START = "__start__"
        END   = "__end__"

from schemas.agent_state_schema import AgentState
from supervisor.supervisor_graph import supervisor_node
from agents.market_agent.graph import market_agent_node
from agents.financial_agent.graph import financial_agent_node
from agents.knowledge_agent.graph import knowledge_agent_node
from agents.strategy_agent.graph import strategy_agent_node
from agents.communication_agent.graph import communication_agent_node


def build_decision_graph():
    builder = StateGraph(AgentState)

    builder.add_node("supervisor",          supervisor_node)
    builder.add_node("market_agent",        market_agent_node)
    builder.add_node("financial_agent",     financial_agent_node)
    builder.add_node("knowledge_agent",     knowledge_agent_node)
    builder.add_node("strategy_agent",      strategy_agent_node)
    builder.add_node("communication_agent", communication_agent_node)

    # Parallel fan-out from supervisor
    builder.add_edge(START,        "supervisor")
    builder.add_edge("supervisor", "market_agent")
    builder.add_edge("supervisor", "financial_agent")
    builder.add_edge("supervisor", "knowledge_agent")

    # All three must complete → strategy (LangGraph waits for all incoming edges)
    builder.add_edge("market_agent",    "strategy_agent")
    builder.add_edge("financial_agent", "strategy_agent")
    builder.add_edge("knowledge_agent", "strategy_agent")

    # Sequential synthesis
    builder.add_edge("strategy_agent",      "communication_agent")
    builder.add_edge("communication_agent", END)

    return builder.compile()
