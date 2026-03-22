from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class DecisionRequest(BaseModel):
    user_query: str = Field(..., example="Should RA Groups expand its AI-based SME lending into UAE?")
    market: str = Field(..., example="UAE")
    company_name: Optional[str] = Field(default="RA Groups")
    budget: Optional[float] = Field(default=1_000_000)
    timeline_months: Optional[int] = Field(default=12)


class DecisionResponse(BaseModel):
    request_id: str
    decision: Dict
    market_insights: Dict
    financial_analysis: Dict
    knowledge_summary: Dict
    final_report: str


class WebSocketRequest(BaseModel):
    user_query: str
    market: str
    budget: Optional[float] = 1_000_000
    timeline_months: Optional[int] = 12
