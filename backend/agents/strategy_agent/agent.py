import json
from langchain_core.messages import SystemMessage, HumanMessage
from config.llm_config import get_reasoning_llm
from agents.strategy_agent.prompt import STRATEGY_SYSTEM_PROMPT


async def run_strategy_agent(
    user_query: str,
    market: str,
    market_insights: dict,
    financial_analysis: dict,
    knowledge_summary: dict,
) -> dict:
    """
    Strategy agent uses the powerful reasoning LLM (gpt-4o) to synthesize
    all three analysis inputs into a final GO / NO-GO decision.
    No tools needed — pure chain-of-thought reasoning over structured data.
    """

    llm = get_reasoning_llm()

    messages = [
        SystemMessage(content=STRATEGY_SYSTEM_PROMPT),
        HumanMessage(content=(
            f"Business Decision Query: {user_query}\n"
            f"Target Market: {market}\n\n"
            "=== MARKET ANALYSIS ===\n"
            f"{json.dumps(market_insights, indent=2)}\n\n"
            "=== FINANCIAL ANALYSIS ===\n"
            f"{json.dumps(financial_analysis, indent=2)}\n\n"
            "=== INTERNAL KNOWLEDGE & STRATEGIC FIT ===\n"
            f"{json.dumps(knowledge_summary, indent=2)}\n\n"
            "Now synthesize all three analyses. Think step by step through each "
            "scoring dimension. Then return the JSON decision."
        ))
    ]

    response = await llm.ainvoke(messages)
    return response.content.strip()
