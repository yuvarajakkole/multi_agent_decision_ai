from langchain.tools import tool


# ---------------------------------------------------------
# QUERY CLASSIFIER
# ---------------------------------------------------------

@tool
def classify_query_type(query: str) -> str:
    """Classify the query into one of the following types:
    - market_expansion
    - product_launch
    - investment_analysis
    - general_business
    """
    text = query.lower()

    if "expand" in text or "market" in text:
        return "market_expansion"

    if "product" in text:
        return "product_launch"

    if "investment" in text:
        return "investment_analysis"

    return "general_business"


# ---------------------------------------------------------
# EXECUTION PLAN GENERATOR
# ---------------------------------------------------------

@tool
def build_execution_plan(query_type: str):
    """Build execution plan based on query type."""
    if query_type == "market_expansion":

        return [
            "market_agent",
            "financial_agent",
            "knowledge_agent",
            "strategy_agent",
            "communication_agent"
        ]

    if query_type == "investment_analysis":

        return [
            "financial_agent",
            "strategy_agent",
            "communication_agent"
        ]

    return [
        "market_agent",
        "financial_agent",
        "knowledge_agent",
        "strategy_agent",
        "communication_agent"
    ]