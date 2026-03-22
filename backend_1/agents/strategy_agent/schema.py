from pydantic import BaseModel
from typing import List


class StrategyDecision(BaseModel):

    decision: str

    confidence: float

    final_score: float

    market_score: float

    financial_score: float

    strategic_fit_score: float

    rationale: List[str]

    risks: List[str]

    next_steps: List[str]