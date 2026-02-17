# app/nodes/strategy_planning.py
# Strategy Planning Agent: synthesizes all agent outputs.

from typing import Dict
from langchain_core.runnables import RunnableConfig
from ..llm import get_llm
from ..models import DecisionState


def strategy_planning_node(state: DecisionState, config: RunnableConfig) -> DecisionState:
    """
    Combines Market, Financial, and Knowledge insights
    into one strategic recommendation for RA Groups.
    """
    llm = get_llm()

    business_query = state.get("business_query", "")
    market_insights = state.get("market_insights", {})
    financial_analysis = state.get("financial_analysis", {})
    knowledge_summary = state.get("knowledge_summary", {})
    
    prompt = f"""
You are the Chief Strategy Officer for RA Groups.

Business question: {business_query}

[MARKET INSIGHTS]
{market_insights}

[FINANCIAL ANALYSIS]
{financial_analysis}

[KNOWLEDGE SUMMARY]
{knowledge_summary}

RA Groups internal benchmarks from the dataset:
- target_min_project_irr_percent: 18
- target_min_2_year_roi_percent: 25
- max_acceptable_npl_ratio_percent: 4
- min_ebit_margin_percent_after_3_years: 20
- max_single_market_investment_usd: 5000000

IMPORTANT DECISION RULES (you must follow these):
- If projected returns are clearly below benchmarks, or risk is High, you should prefer "WAIT" or "NO_GO".
- If the opportunity is attractive but needs prerequisites (partnerships, regulatory clarity, more data), use "GO_WITH_CONDITIONS".
- Only use "GO" when:
  - returns are at or above benchmarks,
  - risks are Low or clearly mitigated,
  - RA Groups has strong strategic fit and resources.
- If information is very incomplete or contradictory, prefer "WAIT".

Now:
1. Choose exactly ONE decision among:
   - "GO"
   - "GO_WITH_CONDITIONS"
   - "WAIT"
   - "NO_GO"

2. Return a JSON-like dictionary:

{{
  "decision": "...",
  "confidence_percent": <0-100>,
  "strategic_rationale": [... 4-7 bullets],
  "key_risks": [... 4-7 bullets],
  "key_opportunities": [... 4-7 bullets],
  "must_do_actions_before_launch": [... 3-7 bullets],
  "suggested_timeline_months": <int>,
  "summary_statement": "<2-4 sentences>"
}}

Be strict: if the case looks weak or very uncertain, do NOT choose "GO_WITH_CONDITIONS" by default.
"""


#     prompt = f"""
# You are the Chief Strategy Officer for RA Groups.

# Business question: {business_query}

# [MARKET INSIGHTS]
# {market_insights}

# [FINANCIAL ANALYSIS]
# {financial_analysis}

# [KNOWLEDGE SUMMARY]
# {knowledge_summary}

# Task:
# 1. Choose one recommendation:
#    - "GO"
#    - "GO_WITH_CONDITIONS"
#    - "WAIT"
#    - "NO_GO"

# 2. Return a JSON-like dictionary with:
#    - decision (one of the four above)
#    - confidence_percent (0-100)
#    - strategic_rationale (4-7 bullet points)
#    - key_risks (4-7 bullet points)
#    - key_opportunities (4-7 bullet points)
#    - must_do_actions_before_launch (3-7 bullet points)
#    - suggested_timeline_months (integer)
#    - summary_statement (2-4 sentences)

# Keep it realistic for a financial services / fintech company.
# Output plain text that looks like JSON.
#     """

    answer = llm.invoke(prompt)

    result: Dict = {"raw_text": answer.content}

    return {"strategy_recommendation": result}
