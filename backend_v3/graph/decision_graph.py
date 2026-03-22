from langgraph.graph import StateGraph
try: from langgraph.graph import START, END
except ImportError:
    try: from langgraph.constants import START, END
    except: START="__start__"; END="__end__"
from schemas.agent_state_schema import AgentState
from supervisor.supervisor_graph import supervisor_node
from agents.market_agent.graph import market_agent_node
from agents.financial_agent.graph import financial_agent_node
from agents.knowledge_agent.graph import knowledge_agent_node
from agents.strategy_agent.graph import strategy_agent_node
from agents.communication_agent.graph import communication_agent_node

def build_decision_graph():
    b=StateGraph(AgentState)
    b.add_node("supervisor",supervisor_node)
    b.add_node("market_agent",market_agent_node)
    b.add_node("financial_agent",financial_agent_node)
    b.add_node("knowledge_agent",knowledge_agent_node)
    b.add_node("strategy_agent",strategy_agent_node)
    b.add_node("communication_agent",communication_agent_node)
    b.add_edge(START,"supervisor")
    # Parallel fan-out
    b.add_edge("supervisor","market_agent")
    b.add_edge("supervisor","financial_agent")
    b.add_edge("supervisor","knowledge_agent")
    # All three → strategy
    b.add_edge("market_agent","strategy_agent")
    b.add_edge("financial_agent","strategy_agent")
    b.add_edge("knowledge_agent","strategy_agent")
    b.add_edge("strategy_agent","communication_agent")
    b.add_edge("communication_agent",END)
    return b.compile()
