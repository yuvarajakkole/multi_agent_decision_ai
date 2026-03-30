"""schemas/api_models.py"""

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class DecisionRequest(BaseModel):
    user_query:       str   = Field(..., example="Should RA Groups expand SME lending into UAE?")
    market:           str   = Field(..., example="UAE")
    company_name:     Optional[str]   = "RA Groups"
    budget:           Optional[float] = 1_000_000
    timeline_months:  Optional[int]   = 12


class OutcomeRequest(BaseModel):
    request_id:      str
    actual_outcome:  str   # "success" | "failure" | "partial"
    notes:           Optional[str] = ""


class DecisionResponse(BaseModel):
    request_id:          str
    decision:            Dict[str, Any]
    confidence_report:   Dict[str, Any]
    market_insights:     Dict[str, Any]
    financial_analysis:  Dict[str, Any]
    knowledge_summary:   Dict[str, Any]
    final_report:        str
    execution_log:       List[Dict]
    loop_summary:        Dict[str, Any]
