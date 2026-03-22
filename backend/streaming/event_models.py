from pydantic import BaseModel
from typing import Optional, Dict


class StreamEvent(BaseModel):
    event: str
    agent: Optional[str] = None
    message: Optional[str] = None
    data: Optional[Dict] = None


class AgentStartEvent(StreamEvent):
    event: str = "agent_start"


class ToolCallEvent(StreamEvent):
    event: str = "tool_call"


class AgentCompleteEvent(StreamEvent):
    event: str = "agent_complete"


class ErrorEvent(StreamEvent):
    event: str = "error"


class FinalResultEvent(StreamEvent):
    event: str = "final_result"
