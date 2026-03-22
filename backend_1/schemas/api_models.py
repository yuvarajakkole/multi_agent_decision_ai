from pydantic import BaseModel, Field
from typing import Dict, List, Optional


# ---------------------------------------------------------
# HTTP REQUEST MODEL
# ---------------------------------------------------------

class DecisionRequest(BaseModel):
    """
    Incoming user request from frontend.
    """

    user_query: str = Field(
        ...,
        example="Should RA Groups expand its AI-based SME lending platform into UAE?"
    )

    market: str = Field(
        ...,
        example="UAE"
    )

    company_name: Optional[str] = Field(
        default="RA Groups"
    )

    budget: Optional[float] = Field(
        default=1000000
    )

    timeline_months: Optional[int] = Field(
        default=12
    )


# ---------------------------------------------------------
# FINAL DECISION OUTPUT
# ---------------------------------------------------------

class DecisionOutput(BaseModel):

    decision: str
    confidence: float

    summary: str

    rationale: List[str]

    risks: List[str]

    next_steps: List[str]


# ---------------------------------------------------------
# HTTP RESPONSE MODEL
# ---------------------------------------------------------

class DecisionResponse(BaseModel):

    request_id: str

    decision: DecisionOutput

    market_insights: Dict

    financial_analysis: Dict

    knowledge_summary: Dict

    final_report: str


# ---------------------------------------------------------
# WEBSOCKET MESSAGE MODELS
# ---------------------------------------------------------

class WebSocketRequest(BaseModel):

    request_id: str

    user_query: str

    market: str


class WebSocketAgentEvent(BaseModel):

    event: str

    agent: str

    message: Optional[str] = None

    data: Optional[Dict] = None


class WebSocketFinalEvent(BaseModel):

    event: str = "final_result"

    decision: Dict

    final_report: str