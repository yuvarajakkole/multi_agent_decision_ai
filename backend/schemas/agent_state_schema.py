from typing import Dict, List, Optional
from typing_extensions import TypedDict


# ---------------------------------------------------------
# GLOBAL AGENT STATE
# Shared across all graph nodes. Each agent reads from
# this state and writes its output back into it.
# FIX: Added next_agent and supervisor_plan which were
# missing but used in supervisor_graph.py — caused KeyError.
# ---------------------------------------------------------

class AgentState(TypedDict, total=False):

    # --------------------------------------------------
    # INPUT FIELDS
    # --------------------------------------------------

    request_id: str          # unique ID for this request
    user_query: str          # raw question from user
    market: str              # target market / location
    company_name: str        # company making the decision
    budget: float            # available budget (USD)
    timeline_months: int     # planning horizon

    # --------------------------------------------------
    # SUPERVISOR OUTPUTS
    # FIX: next_agent and supervisor_plan were missing,
    # causing KeyError when supervisor tried to write them.
    # --------------------------------------------------

    agents_to_run: Optional[List[str]]   # full ordered list
    execution_plan: Optional[Dict]       # structured plan
    next_agent: Optional[str]            # FIXED: first agent to run
    supervisor_plan: Optional[str]       # FIXED: supervisor reasoning text

    # --------------------------------------------------
    # ANALYSIS AGENT OUTPUTS
    # --------------------------------------------------

    market_insights: Optional[Dict]
    financial_analysis: Optional[Dict]
    knowledge_summary: Optional[Dict]

    # --------------------------------------------------
    # STRATEGY OUTPUT
    # --------------------------------------------------

    strategy_decision: Optional[Dict]

    # --------------------------------------------------
    # FINAL REPORT
    # --------------------------------------------------

    final_report: Optional[str]
