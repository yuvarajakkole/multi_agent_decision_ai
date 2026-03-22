import json
import re
from agents.strategy_agent.agent import run_strategy_agent
from streaming.agent_step_streamer import stream_agent_start, stream_agent_complete


# ---------------------------------------------------------
# STRATEGY AGENT NODE
# Receives all three analysis outputs from shared state,
# calls gpt-4o to synthesize into a final decision.
# No tools — pure reasoning over structured inputs.
# ---------------------------------------------------------

async def strategy_agent_node(state: dict) -> dict:

    print("\n========== STRATEGY AGENT NODE START ==========")

    request_id  = state["request_id"]
    user_query  = state["user_query"]
    market      = state.get("market", "unknown market")

    market_insights    = state.get("market_insights", {})
    financial_analysis = state.get("financial_analysis", {})
    knowledge_summary  = state.get("knowledge_summary", {})

    await stream_agent_start(request_id, "strategy_agent")

    raw = await run_strategy_agent(
        user_query=user_query,
        market=market,
        market_insights=market_insights,
        financial_analysis=financial_analysis,
        knowledge_summary=knowledge_summary,
    )

    print(f"Strategy agent raw output: {raw}")

    strategy_decision = _parse_json_output(raw)

    print(f"Strategy decision: {strategy_decision}")

    await stream_agent_complete(request_id, "strategy_agent", strategy_decision)

    print("========== STRATEGY AGENT NODE END ==========\n")

    return {"strategy_decision": strategy_decision}


def _parse_json_output(raw: str) -> dict:
    """Parse JSON from LLM output with a reliable fallback decision."""
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

    # Fallback — conservative WAIT decision when parsing fails
    return {
        "decision": "WAIT",
        "confidence_score": 40,
        "market_score": 15,
        "financial_score": 15,
        "strategic_score": 10,
        "risk_adjustment": -5,
        "total_score": 35,
        "rationale": [
            "Insufficient data to produce a confident recommendation.",
            "Manual review of market, financial, and strategic inputs is required."
        ],
        "key_risks": ["Incomplete analysis data"],
        "conditions": [],
        "next_steps": [
            "Conduct manual due diligence",
            "Gather additional market intelligence",
            "Re-run analysis with complete data inputs"
        ],
        "summary": (
            "The automated analysis could not produce a definitive recommendation. "
            "A conservative WAIT decision is issued pending manual review."
        )
    }
