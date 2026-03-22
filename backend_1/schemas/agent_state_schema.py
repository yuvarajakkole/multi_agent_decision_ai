from typing import Dict, Optional
from typing_extensions import TypedDict


# ---------------------------------------------------------
# GLOBAL AGENT STATE
# ---------------------------------------------------------

class AgentState(TypedDict, total=False):

    # -----------------------------------------------------
    # INPUT
    # -----------------------------------------------------

    request_id: str

    user_query: str

    market: str

    company_name: str

    budget: float

    timeline_months: int


    # -----------------------------------------------------
    # SUPERVISOR OUTPUT
    # -----------------------------------------------------

    agents_to_run: Optional[list]

    execution_plan: Optional[Dict]


    # -----------------------------------------------------
    # AGENT OUTPUTS
    # -----------------------------------------------------

    market_insights: Optional[Dict]

    financial_analysis: Optional[Dict]

    knowledge_summary: Optional[Dict]


    # -----------------------------------------------------
    # STRATEGY OUTPUT
    # -----------------------------------------------------

    strategy_decision: Optional[Dict]


    # -----------------------------------------------------
    # FINAL COMMUNICATION
    # -----------------------------------------------------

    final_report: Optional[str]