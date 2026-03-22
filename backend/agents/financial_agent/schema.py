from pydantic import BaseModel
from typing import List, Dict


class MacroIndicators(BaseModel):
    interest_rate: str
    inflation_rate: str
    gdp_growth: str
    currency_stability: str


class FinancialAnalysis(BaseModel):
    market: str
    estimated_roi_percent: float
    estimated_irr_percent: float
    payback_period_months: int
    risk_level: str                   # Low | Medium | High
    risk_factors: List[str]
    meets_roi_threshold: bool
    meets_irr_threshold: bool
    macro_indicators: Dict
    financial_attractiveness: str     # Low | Medium | High | Strong
    summary: str
