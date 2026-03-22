from pydantic import BaseModel
from typing import List


class MarketInsights(BaseModel):
    market: str
    product: str
    market_size_usd: str
    growth_rate_percent: str
    competition_level: str                 # Low | Medium | High
    key_competitors: List[str]
    regulatory_environment: str            # Supportive | Neutral | Restrictive
    key_regulatory_notes: str
    market_trends: List[str]
    market_attractiveness: str             # Low | Medium | High
    summary: str
