from pydantic import BaseModel
from typing import List


class FinalReport(BaseModel):

    decision: str

    confidence: float

    executive_summary: str

    market_analysis: str

    financial_insights: str

    strategic_fit: str

    risks: List[str]

    recommendations: List[str]