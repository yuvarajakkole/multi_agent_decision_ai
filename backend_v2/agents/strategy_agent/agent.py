import json
from langchain_core.messages import SystemMessage, HumanMessage
from config.llm_config import get_reasoning_llm

_SYSTEM = """
You are a senior corporate strategy executive synthesising three specialist analyses.
You receive real market, financial, and strategic data gathered by other agents.

Your job:
1. Weigh all three analyses.
2. Compute a weighted total_score (0-100):
   - market_attractiveness contributes 30 %
   - financial_attractiveness contributes 40 %
   - strategic_fit contributes 30 %
3. Map total_score to decision:
   >= 75 = GO | 55-74 = GO_WITH_CONDITIONS | 35-54 = WAIT | < 35 = NO_GO
4. Return ONLY JSON:

{
  "decision": "GO|GO_WITH_CONDITIONS|WAIT|NO_GO",
  "confidence_score": 0-100,
  "total_score": 0-100,
  "market_component_score": 0-30,
  "financial_component_score": 0-40,
  "strategic_component_score": 0-30,
  "rationale": ["reason 1", "reason 2", "reason 3"],
  "key_risks": ["risk 1", "risk 2"],
  "conditions": ["condition if GO_WITH_CONDITIONS, else []"],
  "next_steps": ["step 1", "step 2", "step 3"],
  "summary": "one paragraph executive summary"
}

No markdown. Raw JSON only.
"""


async def run_strategy_agent(
    user_query: str, market: str,
    market_insights: dict, financial_analysis: dict, knowledge_summary: dict,
) -> str:
    llm  = get_reasoning_llm()
    prompt = (
        f"User Query: {user_query}\n"
        f"Target Market: {market}\n\n"
        f"MARKET ANALYSIS:\n{json.dumps(market_insights, indent=2)}\n\n"
        f"FINANCIAL ANALYSIS:\n{json.dumps(financial_analysis, indent=2)}\n\n"
        f"STRATEGIC / KNOWLEDGE ANALYSIS:\n{json.dumps(knowledge_summary, indent=2)}\n\n"
        "Synthesise and return the JSON decision."
    )
    resp = await llm.ainvoke([SystemMessage(content=_SYSTEM), HumanMessage(content=prompt)])
    return resp.content
