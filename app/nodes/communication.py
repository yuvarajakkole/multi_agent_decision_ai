# app/nodes/communication.py
# Communication Agent: formats final Markdown report.
from langchain_core.runnables import RunnableConfig
from ..llm import get_llm
from ..models import DecisionState

def communication_node(state: DecisionState, config: RunnableConfig) -> DecisionState:
    """
    Generates a final, human-friendly Markdown decision report for RA Groups.
    """
    llm = get_llm()

    business_query = state.get("business_query", "")
    market = state.get("market", "")
    company_name = state.get("company_name", "RA Groups")

    market_insights = state.get("market_insights", {})
    financial_analysis = state.get("financial_analysis", {})
    knowledge_summary = state.get("knowledge_summary", {})
    strategy_reco = state.get("strategy_recommendation", {})

    prompt = f"""
You are the Executive Communication Agent for {company_name}.

Business question: {business_query}
Target market: {market}

[MARKET INSIGHTS]
{market_insights}

[FINANCIAL ANALYSIS]
{financial_analysis}

[KNOWLEDGE SUMMARY]
{knowledge_summary}

[STRATEGY RECOMMENDATION]
{strategy_reco}

Create a concise MARKDOWN report with sections:

# RA Groups Decision Report

## Executive Summary
- 3-4 bullet points summarising the decision
- Explicitly state final recommendation and confidence

## Market Overview
Summarize key market points and attractiveness.

## Financial Assessment
Summarize investment, returns, and risks.

## Company Fit & Readiness
Summarize strengths, weaknesses, and resource fit.

## Risks & Opportunities
Bullets for each category.

## Recommended Action Plan
A numbered list of steps with approximate timeline.

Keep under ~700 words, professional, C-level friendly.
    """

    answer = llm.invoke(prompt)

    return {"final_report_markdown": answer.content}
