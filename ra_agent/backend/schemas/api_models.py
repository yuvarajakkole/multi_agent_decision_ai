"""schemas/api_models.py

Fixed: budget and timeline_months default to None (not 1_000_000 / 12).
Supervisor extracts these from query text.  If caller explicitly provides them
they are used, otherwise 0 is passed and supervisor extracts from query.
"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class DecisionRequest(BaseModel):
    user_query:      str            = Field(..., example="Should RA Groups expand SME lending into UAE?")
    market:          Optional[str]  = Field(None, example="UAE")
    company_name:    Optional[str]  = "RA Groups"
    budget:          Optional[float]= Field(None, description="Budget in USD. If omitted, extracted from query text.")
    timeline_months: Optional[int]  = Field(None, description="Timeline in months. If omitted, extracted from query.")


class OutcomeRequest(BaseModel):
    request_id:     str
    actual_outcome: str    # "success" | "failure" | "partial"
    notes:          Optional[str] = ""


class DecisionResponse(BaseModel):
    request_id:         str
    decision:           Dict[str, Any]
    confidence_report:  Dict[str, Any]
    market_insights:    Dict[str, Any]
    financial_analysis: Dict[str, Any]
    knowledge_summary:  Dict[str, Any]
    final_report:       str
    execution_log:      List[Dict]
    loop_summary:       Dict[str, Any]
    supervisor_warnings: List[str] = []
