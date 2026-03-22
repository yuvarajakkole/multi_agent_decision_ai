# Legacy tools — no longer used; supervisor now calls LLM directly.
# Kept to avoid import errors in any remaining references.
from langchain_core.tools import tool

@tool
def classify_query_type(query: str) -> str:
    """Classify query type."""
    text = query.lower()
    if "expand" in text or "market" in text: return "market_expansion"
    if "investment" in text: return "investment_analysis"
    return "general_business"

@tool
def build_execution_plan(query_type: str) -> list:
    """Return default execution plan."""
    return ["market_agent","financial_agent","knowledge_agent","strategy_agent","communication_agent"]
