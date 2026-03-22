from pydantic import BaseModel
from typing import List


class StrategyDecision(BaseModel):
    decision: str                   # GO | GO_WITH_CONDITIONS | WAIT | NO_GO
    confidence_score: float
    market_score: float
    financial_score: float
    strategic_score: float
    risk_adjustment: float
    total_score: float
    rationale: List[str]
    key_risks: List[str]
    conditions: List[str]
    next_steps: List[str]
    summary: str
