from pydantic import BaseModel
from typing import Optional, Dict


# ---------------------------------------------------------
# BASE EVENT
# ---------------------------------------------------------

class StreamEvent(BaseModel):

    event: str

    agent: Optional[str] = None

    message: Optional[str] = None

    data: Optional[Dict] = None


# ---------------------------------------------------------
# AGENT START EVENT
# ---------------------------------------------------------

class AgentStartEvent(StreamEvent):

    event: str = "agent_start"


# ---------------------------------------------------------
# AGENT TOOL EVENT
# ---------------------------------------------------------

class ToolCallEvent(StreamEvent):

    event: str = "tool_call"


# ---------------------------------------------------------
# AGENT COMPLETED EVENT
# ---------------------------------------------------------

class AgentCompleteEvent(StreamEvent):

    event: str = "agent_complete"


# ---------------------------------------------------------
# ERROR EVENT
# ---------------------------------------------------------

class ErrorEvent(StreamEvent):

    event: str = "error"


# ---------------------------------------------------------
# FINAL RESULT EVENT
# ---------------------------------------------------------

class FinalResultEvent(StreamEvent):

    event: str = "final_result"