from typing import Dict, List, Optional, Any
from typing_extensions import TypedDict

class AgentState(TypedDict, total=False):
    request_id:str; user_query:str; market:str; company_name:str; budget:float; timeline_months:int
    agents_to_run:Optional[List[str]]; execution_plan:Optional[Dict]
    next_agent:Optional[str]; supervisor_plan:Optional[str]
    _detected_product:Optional[str]; _detected_market:Optional[str]
    market_insights:Optional[Dict]; financial_analysis:Optional[Dict]
    knowledge_summary:Optional[Dict]; strategy_decision:Optional[Dict]; final_report:Optional[str]
    _market_agent_envelope:Optional[Dict]; _financial_agent_envelope:Optional[Dict]
    _knowledge_agent_envelope:Optional[Dict]; _strategy_agent_envelope:Optional[Dict]
    _confidence_report:Optional[Dict]; _final_confidence:Optional[float]; _confidence_adjustment:Optional[float]
    _trace:Optional[Any]; _decision_trace:Optional[Dict]
