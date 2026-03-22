from langchain_core.tools import tool

@tool
def classify_query_type(query: str) -> str:
    """Classify the user query into a business decision type.
    Returns one of: market_expansion, product_launch, investment_analysis, general_business.
    """
    text = query.lower()
    if any(w in text for w in ["expand", "launch", "enter", "new market"]):
        return "market_expansion"
    if "product" in text:
        return "product_launch"
    if "invest" in text:
        return "investment_analysis"
    return "general_business"


@tool
def build_execution_plan(query_type: str) -> list:
    """Build the ordered agent execution plan based on query type.
    Returns a list of agent names in execution order.
    """
    # All query types use the full pipeline. 
    # Future: skip agents for simpler queries to save cost.
    return [
        "market_agent",
        "financial_agent",
        "knowledge_agent",
        "strategy_agent",
        "communication_agent"
    ]
