"""agents/knowledge_agent/schema.py"""

from pydantic import BaseModel
from typing import List, Optional


class KnowledgeSummary(BaseModel):
    company_name:                   str
    strategic_fit:                  Optional[str]  = None
    strategic_fit_reasoning:        Optional[str]  = None
    available_budget_usd:           Optional[float] = None
    budget_within_policy:           Optional[bool] = None
    max_policy_investment_usd:      Optional[float] = None
    risk_appetite:                  Optional[str]  = None
    risk_appetite_match:            Optional[str]  = None
    company_strengths:              List[str]       = []
    company_weaknesses:             List[str]       = []
    past_expansions:                List[dict]      = []
    has_experience_in_this_market:  Optional[bool] = None
    kpi_benchmarks:                 Optional[dict] = None
    relevant_products:              List[str]       = []
    strategic_objective_alignment:  List[str]       = []
    bandwidth_assessment:           Optional[str]  = None
    internal_recommendation:        Optional[str]  = None
    summary:                        Optional[str]  = None
