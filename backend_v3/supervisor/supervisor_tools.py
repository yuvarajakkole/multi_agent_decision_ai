from langchain_core.tools import tool
@tool
def classify_query_type(query: str) -> str:
    "Legacy stub"
    return "market_expansion"
