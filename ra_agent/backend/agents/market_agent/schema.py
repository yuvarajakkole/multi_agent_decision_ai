"""agents/market_agent/schema.py — Output schema for the market agent."""

from pydantic import BaseModel, Field
from typing import List, Optional


class MarketInsights(BaseModel):
    market:               str
    product:              str
    product_class:        str
    country_code:         str
    population:           Optional[int]  = None
    currency:             Optional[str]  = None
    gdp_growth_pct:       Optional[float] = None
    inflation_pct:        Optional[float] = None
    lending_rate_pct:     Optional[float] = None
    market_size:          Optional[str]  = None
    annual_growth_pct:    Optional[float] = None
    market_maturity:      Optional[str]  = None
    competition_level:    Optional[str]  = None
    competitor_types:     List[str]      = Field(default_factory=list)
    regulatory_env:       Optional[str]  = None
    key_regulatory_notes: Optional[str]  = None
    market_trends:        List[str]      = Field(default_factory=list)
    attractiveness_score: Optional[float] = None
    go_signal:            Optional[str]  = None
    opportunities:        List[str]      = Field(default_factory=list)
    threats:              List[str]      = Field(default_factory=list)
    data_quality:         Optional[str]  = None
    data_sources_used:    List[str]      = Field(default_factory=list)
    summary:              Optional[str]  = None
