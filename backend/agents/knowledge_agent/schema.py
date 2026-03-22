from pydantic import BaseModel
from typing import List, Dict, Optional


class PastExpansion(BaseModel):
    market: str
    year: int
    status: str
    roi_percent: Optional[float]
    key_lesson: str


class KnowledgeSummary(BaseModel):
    company_name: str
    query_alignment: str
    company_strengths: List[str]
    relevant_past_expansions: List[Dict]
    available_budget_usd: float
    budget_within_limits: bool
    strategic_objectives_alignment: List[str]
    risk_appetite_match: str
    strategic_fit: str
    recommendation_from_knowledge: str
    summary: str
