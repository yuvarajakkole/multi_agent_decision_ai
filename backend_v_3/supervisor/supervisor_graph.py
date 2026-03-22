"""
supervisor/supervisor_graph.py
Dynamic orchestration: LLM produces structured JSON plan.
Initialises DecisionTrace for the full pipeline.
"""
import json
from langchain_core.messages import SystemMessage, HumanMessage
from config.llm_config import get_fast_llm
from core.trace.decision_trace import DecisionTrace
from streaming.agent_step_streamer import stream_agent_start, stream_agent_complete

_SYSTEM = """
You are the orchestration supervisor of a multi-agent AI decision system.

Given a user query and market, produce a JSON execution plan:

{
  "agents_to_run": ["market_agent","financial_agent","knowledge_agent","strategy_agent","communication_agent"],
  "reasoning": "one sentence explaining why these agents are needed"
}

Rules:
- Always include market_agent, financial_agent, knowledge_agent, strategy_agent, communication_agent for expansion/investment queries.
- For pure financial queries (no market mention) you may skip market_agent.
- Output ONLY valid JSON. No markdown fences. No extra text.
"""


async def supervisor_node(state: dict) -> dict:
    print("\n========== SUPERVISOR NODE START ==========")

    request_id = state["request_id"]
    user_query = state["user_query"]
    market     = state.get("market", "")
    budget     = state.get("budget", 0)

    # Initialise trace — flows through entire pipeline
    trace = DecisionTrace(request_id=request_id, user_query=user_query, market=market)
    trace.start_step("supervisor")

    await stream_agent_start(request_id, "supervisor")

    llm  = get_fast_llm()
    resp = await llm.ainvoke([
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=(
            f"Query: {user_query}\n"
            f"Market: {market}\n"
            f"Budget: ${budget:,.0f}"
        )),
    ])

    raw = resp.content.strip()
    print(f"Supervisor raw: {raw}")

    try:
        plan          = json.loads(raw.replace("```json","").replace("```","").strip())
        agents_to_run = plan.get("agents_to_run", [])
        reasoning     = plan.get("reasoning", "")
    except Exception:
        agents_to_run = ["market_agent","financial_agent","knowledge_agent",
                         "strategy_agent","communication_agent"]
        reasoning     = "Default pipeline (JSON parse failed)"

    trace.log_step(
        agent="supervisor",
        input_summary={"user_query": user_query, "market": market},
        output_summary={"agents_to_run": agents_to_run, "reasoning": reasoning},
        confidence=1.0, source="llm", errors=[], warnings=[],
    )

    await stream_agent_complete(request_id, "supervisor",
                                {"agents_to_run": agents_to_run, "reasoning": reasoning})

    print(f"Plan: {agents_to_run}")
    print("========== SUPERVISOR NODE END ==========\n")

    return {
        "agents_to_run":  agents_to_run,
        "next_agent":     agents_to_run[0] if agents_to_run else "market_agent",
        "supervisor_plan": reasoning,
        "execution_plan": {"agents": agents_to_run, "reasoning": reasoning},
        "_trace":         trace,
    }
