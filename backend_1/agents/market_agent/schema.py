from pydantic import BaseModel
from typing import List


class MarketInsights(BaseModel):

    market_size_estimate: str

    growth_rate_estimate: str

    competition_level: str

    market_attractiveness: str

    fintech_trends: List[str]

    competitor_types: List[str]

    regulatory_notes: List[str]

    market_score: float