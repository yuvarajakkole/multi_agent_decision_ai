"""
Strategy Agent — the core decision engine.
Uses a strict scoring rubric to prevent every query getting GO_WITH_CONDITIONS.
The LLM must justify each score component with data from the other agents.
"""
import json
from langchain_core.messages import SystemMessage, HumanMessage
from config.llm_config import get_reasoning_llm

_SYSTEM = """
You are RA Groups' chief strategy officer making a real investment decision.
You will LOSE money if you make a wrong call. Be accurate and honest.

SCORING RUBRIC (total = market + financial + strategic, max 100):

MARKET SCORE (0-40):
  market_attractiveness_score from market agent ÷ 100 × 40
  DEDUCTIONS (apply all that match):
    -5  competition_level = High
    -10 competition_level = Very High
    -8  market_maturity = Mature (harder to enter)
    -5  regulatory_environment = Restrictive
    +5  market_maturity = Emerging or Developing AND gdp_growth > 5%

FINANCIAL SCORE (0-40):
  attractiveness_score from financial agent ÷ 100 × 40
  DEDUCTIONS:
    -8  risk_level = High
    -15 risk_level = Very High
    -5  market_sentiment = Bearish
    -3  inflation_percent > 10
    +5  meets_roi_threshold = true
    +5  meets_irr_threshold = true

STRATEGIC SCORE (0-20):
  Start at 10. Apply:
    +6  strategic_fit = High
    +3  strategic_fit = Medium
    -3  strategic_fit = Low
    +4  has_past_experience_in_this_market = true
    -2  has_past_experience_in_this_market = false
    +2  budget_within_limits = true
    -4  budget_within_limits = false
    +2  risk_appetite_match = Aligned
    -2  risk_appetite_match = Misaligned
    Max 20, Min 0.

FINAL DECISION (apply confidence weighting):
  weighted_total = market_score×market_conf + financial_score×financial_conf + strategic_score×knowledge_conf
  adjusted_total = weighted_total / (market_conf+financial_conf+knowledge_conf) × 100 ... but actually:
  Apply confidence as: final_score = raw_total × (0.4 + 0.6×avg_confidence)

  Thresholds:
  >= 68 → GO           (strong evidence across all dimensions)
  >= 50 → GO_WITH_CONDITIONS  (viable but real issues to address)
  >= 33 → WAIT         (not yet — specific blockers must be resolved)
  <  38 → NO_GO        (fundamental mismatch — do not proceed)

CRITICAL ANTI-BIAS RULES:
- DO NOT default to GO_WITH_CONDITIONS. That is the lazy middle answer.
- If competition is Very High AND market is Mature → likely WAIT or NO_GO
- If market has no past RA Groups experience AND budget is tight → lower score
- If inflation > 15% → always score financial attractiveness as Low regardless of IRR
- High GDP growth alone does NOT make a GO decision — financial viability must also hold
- If total_score < 38, RETURN NO_GO even if you personally think the market sounds interesting
- GO requires STRONG evidence in at least 2 of the 3 dimensions

Return ONLY this JSON:
{
  "decision": "GO|GO_WITH_CONDITIONS|WAIT|NO_GO",
  "confidence_score": <0-100, your confidence in this decision>,
  "total_score": <calculated number>,
  "market_component_score": <0-40>,
  "financial_component_score": <0-40>,
  "strategic_component_score": <0-20>,
  "score_breakdown": {
    "market_base": <market_attractiveness_score/100*40>,
    "market_deductions": <list of deductions applied>,
    "financial_base": <attractiveness_score/100*40>,
    "financial_deductions": <list of deductions applied>,
    "strategic_base": 10,
    "strategic_adjustments": <list of adjustments applied>
  },
  "rationale": [
    "<specific data point from market agent that drove this decision>",
    "<specific data point from financial agent>",
    "<specific data point from knowledge agent>"
  ],
  "key_risks": ["<real risk from data>","<real risk>","<real risk>"],
  "conditions": ["<if GO_WITH_CONDITIONS: specific conditions, else empty list>"],
  "next_steps": ["<specific action 1>","<action 2>","<action 3>"],
  "summary": "<2-3 sentences that explain WHY this specific decision was made — cite actual numbers>"
}
"""

async def run_strategy_agent(user_query, market, market_insights, financial_analysis, knowledge_summary,
                              market_conf, financial_conf, knowledge_conf) -> str:
    llm=get_reasoning_llm()
    prompt=(
        f"User Query: {user_query}\nTarget Market: {market}\n"
        f"Market Agent Confidence: {market_conf}\n"
        f"Financial Agent Confidence: {financial_conf}\n"
        f"Knowledge Agent Confidence: {knowledge_conf}\n\n"
        f"MARKET ANALYSIS:\n{json.dumps(market_insights,indent=2)}\n\n"
        f"FINANCIAL ANALYSIS:\n{json.dumps(financial_analysis,indent=2)}\n\n"
        f"STRATEGIC KNOWLEDGE:\n{json.dumps(knowledge_summary,indent=2)}\n\n"
        "Apply the scoring rubric strictly. Show your score calculations in score_breakdown. Return JSON."
    )
    resp=await llm.ainvoke([SystemMessage(content=_SYSTEM),HumanMessage(content=prompt)])
    return resp.content
