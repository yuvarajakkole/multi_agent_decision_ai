"""agents/financial_agent/schema.py"""

from pydantic import BaseModel
from typing import List, Optional


class FinancialAnalysis(BaseModel):
    market:                    str
    product_class:             str
    base_lending_rate_pct:     Optional[float] = None
    product_gross_yield_pct:   Optional[float] = None
    product_net_yield_pct:     Optional[float] = None
    annual_net_income_usd:     Optional[float] = None
    estimated_roi_pct:         Optional[float] = None
    estimated_irr_pct:         Optional[float] = None
    payback_months:            Optional[int]   = None
    meets_roi_target:          Optional[bool]  = None
    meets_irr_target:          Optional[bool]  = None
    financial_attractiveness:  Optional[str]   = None
    attractiveness_score:      Optional[float] = None
    risk_level:                Optional[str]   = None
    risk_factors:              List[str]        = []
    currency:                  Optional[str]   = None
    exchange_rate_usd:         Optional[float] = None
    currency_stability:        Optional[str]   = None
    inflation_pct:             Optional[float] = None
    gdp_growth_pct:            Optional[float] = None
    market_sentiment:          Optional[str]   = None
    macro_environment:         Optional[str]   = None
    data_quality:              Optional[str]   = None
    summary:                   Optional[str]   = None
