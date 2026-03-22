from pydantic import BaseModel
from typing import List


class FinalReport(BaseModel):
    """
    The communication agent produces a markdown-formatted executive report
    stored as a plain string in final_report on the AgentState.
    This schema is for documentation and validation purposes.
    """
    decision: str
    confidence_score: float
    executive_summary: str
    market_analysis: str
    financial_assessment: str
    strategic_fit: str
    key_risks: List[str]
    conditions: List[str]
    next_steps: List[str]
    full_report_markdown: str
