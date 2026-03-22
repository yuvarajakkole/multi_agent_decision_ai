from graph.decision_graph import build_decision_graph
from streaming.agent_step_streamer import stream_error

# Build graph once at module load — reused for every request
_graph = build_decision_graph()


async def run_graph(state: dict) -> dict:
    """
    Execute the full multi-agent decision graph for a given input state.

    Args:
        state: Initial AgentState dict containing user_query, market,
               budget, timeline_months, request_id, company_name.

    Returns:
        Final AgentState after all agents have run, containing
        market_insights, financial_analysis, knowledge_summary,
        strategy_decision, and final_report.
    """
    try:
        result = await _graph.ainvoke(state)
        return result

    except Exception as e:
        request_id = state.get("request_id", "unknown")
        print(f"Graph runner error [{request_id}]: {e}")

        await stream_error(
            request_id=request_id,
            agent_name="graph_runner",
            error_message=str(e)
        )
        raise
