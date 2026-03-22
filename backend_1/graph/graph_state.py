from typing import Optional, Dict
from typing_extensions import TypedDict


class GraphState(TypedDict, total=False):

    # request information
    request_id: str
    user_query: str
    market: str
    company_name: str
    budget: float
    timeline_months: int

    # supervisor outputs
    execution_plan: Optional[str]

    # agent outputs
    market_insights: Optional[Dict]
    financial_analysis: Optional[Dict]
    knowledge_summary: Optional[Dict]

    # strategy output
    strategy_decision: Optional[Dict]

    # final output
    final_report: Optional[str]