"""agents/strategy_agent/schema.py"""

from pydantic import BaseModel
from typing import List, Optional


class StrategyDecision(BaseModel):
    decision:            str                    # GO | GO_WITH_CONDITIONS | WAIT | NO_GO
    confidence_pct:      Optional[float] = None
    raw_score:           Optional[float] = None
    adjusted_score:      Optional[float] = None
    market_component:    Optional[float] = None
    financial_component: Optional[float] = None
    strategic_component: Optional[float] = None
    score_breakdown:     Optional[dict]  = None
    rationale:           List[str]        = []
    key_risks:           List[str]        = []
    conditions:          List[str]        = []
    blocking_issues:     List[str]        = []
    next_steps:          List[str]        = []
    time_to_reassess_months: Optional[int] = None
    summary:             Optional[str]   = None
