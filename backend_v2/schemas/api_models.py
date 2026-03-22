from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class DecisionRequest(BaseModel):
    user_query:      str   = Field(..., example="Should RA Groups expand SME lending into UAE?")
    market:          str   = Field(..., example="UAE")
    company_name:    Optional[str]   = Field(default="RA Groups")
    budget:          Optional[float] = Field(default=1_000_000)
    timeline_months: Optional[int]   = Field(default=12)


class OutcomeRequest(BaseModel):
    request_id:     str
    actual_outcome: str          # "success" | "failure" | "partial"
    notes:          Optional[str] = ""


class AgentConfidenceBreakdown(BaseModel):
    confidence:   float
    weight:       float
    contribution: float
    is_reliable:  bool
    errors:       List[str]
    source:       str


class ConfidenceReport(BaseModel):
    weighted_confidence: float
    confidence_label:    str
    overall_reliable:    bool
    unreliable_agents:   List[str]
    per_agent:           Dict[str, Any]


class DecisionCore(BaseModel):
    outcome:     str
    total_score: float
    confidence:  float
    rationale:   List[str]
    key_risks:   List[str]
    conditions:  List[str]
    next_steps:  List[str]
    summary:     str


class DecisionResponse(BaseModel):
    request_id:        str
    decision:          DecisionCore
    confidence_report: ConfidenceReport
    market_insights:   Dict
    financial_analysis: Dict
    knowledge_summary: Dict
    final_report:      str
    decision_trace:    Dict
