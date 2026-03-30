"""agents/communication_agent/schema.py"""

from pydantic import BaseModel
from typing import Optional


class FinalReport(BaseModel):
    decision:          str
    score:             Optional[float] = None
    confidence_pct:    Optional[float] = None
    report_markdown:   str
    weighted_confidence: Optional[float] = None
    confidence_label:  Optional[str]  = None
