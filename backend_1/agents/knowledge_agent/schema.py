from pydantic import BaseModel
from typing import List


class KnowledgeSummary(BaseModel):

    company_strengths: List[str]

    company_weaknesses: List[str]

    past_expansion_markets: List[str]

    strategic_fit_score: float

    financial_health_summary: str

    resource_capacity_score: float