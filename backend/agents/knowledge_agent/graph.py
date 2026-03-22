import json
import re
from agents.knowledge_agent.agent import run_knowledge_agent
from streaming.agent_step_streamer import stream_agent_start, stream_agent_complete


async def knowledge_agent_node(state: dict) -> dict:

    print("\n========== KNOWLEDGE AGENT NODE START ==========")

    request_id = state["request_id"]
    user_query = state["user_query"]
    market     = state.get("market", "unknown market")
    budget     = state.get("budget", 1_000_000)

    await stream_agent_start(request_id, "knowledge_agent")

    raw = await run_knowledge_agent(
        f"Evaluate the internal strategic fit for this decision:\n"
        f"Query: {user_query}\n"
        f"Target Market: {market}\n"
        f"Requested Budget: ${budget:,.0f}\n\n"
        "Use your tools to retrieve company profile, strategic objectives, "
        "past expansions, financial history, and risk policies. "
        "Then return the JSON output."
    )

    print(f"Knowledge agent raw output: {raw}")
    knowledge_summary = _parse_json(raw)

    await stream_agent_complete(request_id, "knowledge_agent", knowledge_summary)
    print("========== KNOWLEDGE AGENT NODE END ==========\n")

    return {"knowledge_summary": knowledge_summary}


def _parse_json(raw: str) -> dict:
    try:
        cleaned = raw.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except Exception:
        pass
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return {
        "company_name": "RA Groups", "query_alignment": "Medium",
        "company_strengths": ["AI-based underwriting", "Fintech expansion experience"],
        "relevant_past_expansions": [], "available_budget_usd": 3_000_000,
        "budget_within_limits": True, "strategic_objectives_alignment": [],
        "risk_appetite_match": "Aligned", "strategic_fit": "Medium",
        "recommendation_from_knowledge": "Manual internal review recommended.",
        "summary": "Internal knowledge assessment could not be fully completed."
    }