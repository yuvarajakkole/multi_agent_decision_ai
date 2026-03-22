import json
from langchain_core.messages import SystemMessage, HumanMessage
from config.llm_config import get_communication_llm
from agents.communication_agent.prompt import COMMUNICATION_SYSTEM_PROMPT


async def run_communication_agent(
    user_query: str,
    market: str,
    strategy_decision: dict,
    market_insights: dict,
    financial_analysis: dict,
    knowledge_summary: dict,
) -> str:
    """
    Communication agent generates the final executive markdown report.
    Uses gpt-4o at low temperature for polished, consistent output.
    Returns the report as a markdown-formatted string.
    """

    llm = get_communication_llm()

    decision      = strategy_decision.get("decision", "WAIT")
    confidence    = strategy_decision.get("confidence_score", 0)
    rationale     = strategy_decision.get("rationale", [])
    risks         = strategy_decision.get("key_risks", [])
    conditions    = strategy_decision.get("conditions", [])
    next_steps    = strategy_decision.get("next_steps", [])
    dec_summary   = strategy_decision.get("summary", "")

    messages = [
        SystemMessage(content=COMMUNICATION_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Prepare an executive decision report for the following:\n\n"
            f"ORIGINAL QUERY: {user_query}\n"
            f"TARGET MARKET : {market}\n\n"
            "=== STRATEGIC DECISION ===\n"
            f"Decision        : {decision}\n"
            f"Confidence Score: {confidence}/100\n"
            f"Decision Summary: {dec_summary}\n"
            f"Rationale       : {json.dumps(rationale, indent=2)}\n"
            f"Key Risks       : {json.dumps(risks, indent=2)}\n"
            f"Conditions      : {json.dumps(conditions, indent=2)}\n"
            f"Next Steps      : {json.dumps(next_steps, indent=2)}\n\n"
            "=== MARKET ANALYSIS ===\n"
            f"{json.dumps(market_insights, indent=2)}\n\n"
            "=== FINANCIAL ANALYSIS ===\n"
            f"{json.dumps(financial_analysis, indent=2)}\n\n"
            "=== INTERNAL STRATEGIC FIT ===\n"
            f"{json.dumps(knowledge_summary, indent=2)}\n\n"
            "Write the full executive report now following the required structure."
        ))
    ]

    response = await llm.ainvoke(messages)
    return response.content.strip()
