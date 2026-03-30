"""
graph/decision_graph.py

The main LangGraph state machine.

Architecture:
  START
    │
  supervisor                      (extracts product/market, sets routing)
    │
  ┌─┴──────────────────┐
  │         │           │          (PARALLEL fan-out)
market   financial  knowledge
  │         │           │
  └────┬────┘───────────┘
       │
   quality_router                  (checks confidence flags)
       │
   ┌───┴───────────────────┐
   │                       │
retry loop               strategy   (if quality OK)
(back to agents)             │
                         quality_router_2    (checks strategy quality)
                             │
                         ┌───┴───────────┐
                         │               │
                    strategy_retry   communication   (if OK)
                                         │
                                        END

Key design decisions:
- quality_router is a conditional edge function, not a node.
  It reads quality_flags from state to decide where to route.
- Parallel agents (market/financial/knowledge) run in the same "superstep".
- Retry loops are bounded by MAX_AGENT_RETRIES in settings.py.
- Both GO and NO_GO route to communication_agent — all decisions get a report.
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

from schemas.graph_state import AgentState
from supervisor.supervisor_graph       import supervisor_node
from agents.market_agent.graph        import market_agent_node
from agents.financial_agent.graph     import financial_agent_node
from agents.knowledge_agent.graph     import knowledge_agent_node
from agents.strategy_agent.graph      import strategy_agent_node
from agents.communication_agent.graph import communication_agent_node
from config.settings import MAX_AGENT_RETRIES


# ─── Router functions (conditional edges) ────────────────────────────────────

def route_after_supervisor(state: dict) -> str:
    """
    After supervisor, always fan out to parallel research agents.
    """
    return "parallel_research"


def route_after_research(state: dict) -> str:
    """
    After all three research agents complete:
    - If any agent needs a retry AND hasn't exceeded limit → retry that agent
    - Otherwise → go to strategy
    
    LangGraph calls this after ALL parallel nodes in a superstep complete.
    """
    flags   = state.get("quality_flags", {})
    retries = {
        "market":    int(state.get("market_retries",    0)),
        "financial": int(state.get("financial_retries", 0)),
        "knowledge": int(state.get("knowledge_retries", 0)),
    }

    # Check each agent in priority order
    if flags.get("market_needs_retry") and retries["market"] <= MAX_AGENT_RETRIES:
        print(f"[router] market_agent retry #{retries['market']}")
        return "retry_market"

    if flags.get("financial_needs_retry") and retries["financial"] <= MAX_AGENT_RETRIES:
        print(f"[router] financial_agent retry #{retries['financial']}")
        return "retry_financial"

    if flags.get("knowledge_needs_retry") and retries["knowledge"] <= MAX_AGENT_RETRIES:
        print(f"[router] knowledge_agent retry #{retries['knowledge']}")
        return "retry_knowledge"

    # All research complete with acceptable quality
    print("[router] research complete → strategy")
    return "to_strategy"


def route_after_strategy(state: dict) -> str:
    """
    After strategy agent:
    - If strategy needs retry → retry strategy
    - If routing_decision is low_quality_defer → retry all research
    - Otherwise → communication
    """
    flags   = state.get("quality_flags", {})
    retries = int(state.get("strategy_retries", 0))
    routing = state.get("routing_decision", "")

    if routing == "low_quality_defer" and retries <= 1:
        # All research agents had poor data — retry all of them
        print("[router] strategy deferred due to low quality → re-run research")
        return "retry_all_research"

    if flags.get("strategy_needs_retry") and retries <= MAX_AGENT_RETRIES:
        print(f"[router] strategy_agent retry #{retries}")
        return "retry_strategy"

    print("[router] strategy complete → communication")
    return "to_communication"


# ─── Graph construction ────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)

    # ── Register nodes ──────────────────────────────────────────────────────
    builder.add_node("supervisor",         supervisor_node)
    builder.add_node("market_agent",       market_agent_node)
    builder.add_node("financial_agent",    financial_agent_node)
    builder.add_node("knowledge_agent",    knowledge_agent_node)
    builder.add_node("strategy_agent",     strategy_agent_node)
    builder.add_node("communication_agent", communication_agent_node)

    # ── Entry point ──────────────────────────────────────────────────────────
    builder.add_edge(START, "supervisor")

    # ── Supervisor → parallel research (fan-out) ─────────────────────────────
    # All three run simultaneously in one superstep
    builder.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "parallel_research": "market_agent",
        }
    )
    # financial and knowledge also start after supervisor (parallel)
    builder.add_edge("supervisor", "financial_agent")
    builder.add_edge("supervisor", "knowledge_agent")

    # ── Research agents → quality router ─────────────────────────────────────
    # LangGraph waits for ALL three before calling the conditional edge
    builder.add_conditional_edges(
        "market_agent",
        route_after_research,
        {
            "retry_market":    "market_agent",
            "retry_financial": "financial_agent",
            "retry_knowledge": "knowledge_agent",
            "to_strategy":     "strategy_agent",
        }
    )
    builder.add_conditional_edges(
        "financial_agent",
        route_after_research,
        {
            "retry_market":    "market_agent",
            "retry_financial": "financial_agent",
            "retry_knowledge": "knowledge_agent",
            "to_strategy":     "strategy_agent",
        }
    )
    builder.add_conditional_edges(
        "knowledge_agent",
        route_after_research,
        {
            "retry_market":    "market_agent",
            "retry_financial": "financial_agent",
            "retry_knowledge": "knowledge_agent",
            "to_strategy":     "strategy_agent",
        }
    )

    # ── Strategy agent → quality router ──────────────────────────────────────
    builder.add_conditional_edges(
        "strategy_agent",
        route_after_strategy,
        {
            "retry_strategy":     "strategy_agent",
            "retry_all_research": "market_agent",
            "to_communication":   "communication_agent",
        }
    )

    # ── Communication → END ───────────────────────────────────────────────────
    builder.add_edge("communication_agent", END)

    return builder.compile()


# ── Module-level compiled graph instance ─────────────────────────────────────
_graph = None


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
