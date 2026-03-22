import json
from langchain_core.messages import SystemMessage, HumanMessage
from config.llm_config import get_fast_llm
from supervisor.supervisor_prompt import SUPERVISOR_SYSTEM_PROMPT
from streaming.agent_step_streamer import stream_agent_start, stream_agent_complete


# ---------------------------------------------------------
# SUPERVISOR NODE
# FIX 1: Replaced fragile keyword matching with structured
#         JSON output from the LLM — reliable routing.
# FIX 2: Removed dead-code fallback that could never trigger.
# FIX 3: Uses ainvoke (async) instead of invoke (sync).
# FIX 4: next_agent is now always set from the JSON plan.
# ---------------------------------------------------------

async def supervisor_node(state: dict) -> dict:

    print("\n========== SUPERVISOR NODE START ==========")

    request_id = state["request_id"]
    user_query = state["user_query"]
    market = state.get("market", "")
    budget = state.get("budget", 0)

    await stream_agent_start(request_id, "supervisor")

    llm = get_fast_llm()

    messages = [
        SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"User query: {user_query}\n"
            f"Target market: {market}\n"
            f"Budget: ${budget:,.0f}\n\n"
            "Analyze this query and return the JSON execution plan."
        ))
    ]

    response = await llm.ainvoke(messages)
    raw_output = response.content.strip()

    print(f"Supervisor raw output: {raw_output}")

    # Parse JSON from supervisor output
    try:
        # Strip markdown fences if LLM adds them
        cleaned = raw_output.replace("```json", "").replace("```", "").strip()
        plan = json.loads(cleaned)
        agents_to_run = plan.get("agents_to_run", [])
        reasoning = plan.get("reasoning", "")
    except (json.JSONDecodeError, Exception) as e:
        print(f"Supervisor JSON parse failed: {e}. Using default pipeline.")
        agents_to_run = [
            "market_agent",
            "financial_agent",
            "knowledge_agent",
            "strategy_agent",
            "communication_agent"
        ]
        reasoning = "Default pipeline (JSON parse failed)"

    # FIX: next_agent is reliably set from parsed plan, not keyword matching.
    # The decision graph routes supervisor → market_agent → financial_agent → ...
    # next_agent here is informational; actual routing is in decision_graph edges.
    next_agent = agents_to_run[0] if agents_to_run else "market_agent"

    print(f"Agents to run: {agents_to_run}")
    print(f"Next agent: {next_agent}")

    await stream_agent_complete(request_id, "supervisor", {
        "agents_to_run": agents_to_run,
        "reasoning": reasoning
    })

    print("========== SUPERVISOR NODE END ==========\n")

    return {
        "agents_to_run": agents_to_run,
        "next_agent": next_agent,
        "supervisor_plan": reasoning,
        "execution_plan": {"agents": agents_to_run, "reasoning": reasoning}
    }
