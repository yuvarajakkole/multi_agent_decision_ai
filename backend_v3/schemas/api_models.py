from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional

class DecisionRequest(BaseModel):
    user_query:str=Field(...,example="Should RA Groups expand SME lending into UAE?")
    market:str=Field(...,example="UAE")
    company_name:Optional[str]="RA Groups"
    budget:Optional[float]=1_000_000
    timeline_months:Optional[int]=12

class OutcomeRequest(BaseModel):
    request_id:str; actual_outcome:str; notes:Optional[str]=""
