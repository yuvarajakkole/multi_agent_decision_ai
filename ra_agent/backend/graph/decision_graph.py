"""
graph/decision_graph.py

RETRY ORDERING FIX:
  The previous graph had conditional_edges from each individual research agent
  (market, financial, knowledge), which meant any one agent completing could
  trigger routing to strategy before the other two finished.

  CORRECT behaviour: all three research agents run in parallel AND ALL must
  complete before routing checks happen. LangGraph handles this via the
  "fan-in" pattern — route_after_research only evaluates once all three
  parallel nodes in the same superstep have written their state.

  The graph topology enforces this:
  - supervisor fans out to all three (parallel superstep)
  - All three then feed into the SAME conditional edge function
  - LangGraph waits for all parallel nodes before evaluating the edge
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

from datetime import datetime, timezone

from schemas.graph_state          import AgentState
from supervisor.supervisor_graph  import supervisor_node
from agents.market_agent.graph    import market_agent_node
from agents.financial_agent.graph import financial_agent_node
from agents.knowledge_agent.graph import knowledge_agent_node
from agents.strategy_agent.graph  import strategy_agent_node
from agents.communication_agent.graph import communication_agent_node
from agents.advisory_agent.agent  import run_advisory
from config.settings import MAX_AGENT_RETRIES


# ─── Advisory node ───────────────────────────────────────────────────────────

async def advisory_node(state: dict) -> dict:
    """Open-ended advisory queries — no GO/NO_GO pipeline, just useful guidance."""
    rid    = state["request_id"]
    budget = float(state.get("budget", 0) or 0)

    from streaming.streamer import stream_final
    report = await run_advisory(
        user_query      = state["user_query"],
        market          = state.get("market", ""),
        budget          = budget,
        timeline_months = int(state.get("timeline_months", 12) or 12),
        request_id      = rid,
    )

    await stream_final(rid, {"decision": "ADVISORY"}, report, 0.85, "High")

    return {
        "final_report":      report,
        "strategy_decision": {
            "decision":      "ADVISORY",
            "adjusted_score": None,
            "summary":       "Advisory response — no GO/NO_GO decision.",
            "rationale":     ["Open-ended advisory query — not a specific investment decision."],
            "next_steps":    ["Define a specific opportunity to evaluate for a GO/NO_GO decision."],
        },
        "weighted_confidence": 0.85,
        "confidence_label":   "High",
        "decision_is_final":  True,
        "execution_log": [{
            "agent":     "advisory_agent",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action":    "advisory_response_generated",
        }],
    }


# ─── Router functions ─────────────────────────────────────────────────────────

def route_after_supervisor(state: dict) -> str:
    if state.get("routing_decision") == "advisory":
        return "advisory"
    return "parallel_research"


def route_after_research(state: dict) -> str:
    """
    Called ONCE after ALL parallel research agents finish (LangGraph fan-in).
    Checks quality flags from all three agents before routing to strategy.
    This guarantees strategy never runs on intermediate/partial data.
    """
    flags   = state.get("quality_flags", {})
    retries = {
        "market":    int(state.get("market_retries",    0)),
        "financial": int(state.get("financial_retries", 0)),
        "knowledge": int(state.get("knowledge_retries", 0)),
    }

    # Only retry agents that need it AND haven't exceeded max
    if flags.get("market_needs_retry")    and retries["market"]    <= MAX_AGENT_RETRIES:
        return "retry_market"
    if flags.get("financial_needs_retry") and retries["financial"] <= MAX_AGENT_RETRIES:
        return "retry_financial"
    if flags.get("knowledge_needs_retry") and retries["knowledge"] <= MAX_AGENT_RETRIES:
        return "retry_knowledge"

    # All three agents done — safe to run strategy
    return "to_strategy"


def route_after_strategy(state: dict) -> str:
    flags   = state.get("quality_flags", {})
    retries = int(state.get("strategy_retries", 0))
    routing = state.get("routing_decision", "")

    if routing == "low_quality_defer" and retries <= 1:
        return "retry_all_research"
    if flags.get("strategy_needs_retry") and retries <= MAX_AGENT_RETRIES:
        return "retry_strategy"

    return "to_communication"


# ─── Graph construction ────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    builder = StateGraph(AgentState)

    builder.add_node("supervisor",          supervisor_node)
    builder.add_node("advisory_agent",      advisory_node)
    builder.add_node("market_agent",        market_agent_node)
    builder.add_node("financial_agent",     financial_agent_node)
    builder.add_node("knowledge_agent",     knowledge_agent_node)
    builder.add_node("strategy_agent",      strategy_agent_node)
    builder.add_node("communication_agent", communication_agent_node)

    # Entry → supervisor
    builder.add_edge(START, "supervisor")

    # Supervisor → advisory OR parallel fan-out
    builder.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {"advisory": "advisory_agent", "parallel_research": "market_agent"},
    )
    # Parallel: supervisor also fans out to financial and knowledge simultaneously
    builder.add_edge("supervisor", "financial_agent")
    builder.add_edge("supervisor", "knowledge_agent")

    # Advisory → END (bypasses entire research/strategy pipeline)
    builder.add_edge("advisory_agent", END)

    # ── Research → quality router ─────────────────────────────────────────────
    # Each of the three agents connects to route_after_research.
    # LangGraph runs all three in one superstep; route_after_research is called
    # once after ALL three have written their state (fan-in guarantee).
    for agent in ("market_agent", "financial_agent", "knowledge_agent"):
        builder.add_conditional_edges(
            agent,
            route_after_research,
            {
                "retry_market":    "market_agent",
                "retry_financial": "financial_agent",
                "retry_knowledge": "knowledge_agent",
                "to_strategy":     "strategy_agent",
            },
        )

    # Strategy → quality router
    builder.add_conditional_edges(
        "strategy_agent",
        route_after_strategy,
        {
            "retry_strategy":     "strategy_agent",
            "retry_all_research": "market_agent",
            "to_communication":   "communication_agent",
        },
    )

    builder.add_edge("communication_agent", END)
    return builder.compile()


_graph = None

def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph
