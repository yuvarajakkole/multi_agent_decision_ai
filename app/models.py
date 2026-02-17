# app/models.py

from typing import Dict
from typing_extensions import TypedDict
from pydantic import BaseModel, Field


# -------- LangGraph Shared State --------

class DecisionState(TypedDict, total=False):
    """
    Shared state passed between nodes.
    Each node reads & writes parts of this.
    """
    # Input
    business_query: str
    market: str
    company_name: str
    budget: float
    timeline_months: int

    # Outputs from agents
    market_insights: Dict
    financial_analysis: Dict
    knowledge_summary: Dict
    strategy_recommendation: Dict
    final_report_markdown: str


# -------- FastAPI Request/Response Models --------

class DecisionRequest(BaseModel):
    """
    Request body for the /decide endpoint.
    """
    business_query: str = Field(
        ...,
        example="Should RA Groups expand its AI-based lending platform into the UAE market?"
    )
    market: str = Field(..., example="UAE")
    company_name: str = Field("RA Groups", example="RA Groups")
    budget: float = Field(..., example=1000000)
    timeline_months: int = Field(..., example=12)


class DecisionResponse(BaseModel):
    """
    Response body with full decision report and intermediate agent outputs.
    """
    final_report_markdown: str
    strategy_recommendation: Dict
    market_insights: Dict
    financial_analysis: Dict
    knowledge_summary: Dict
