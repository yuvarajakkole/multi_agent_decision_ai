from typing import Optional, Dict
from streaming.websocket_manager import ws_manager
from streaming.event_models import (
    AgentStartEvent,
    AgentCompleteEvent,
    ToolCallEvent,
    ErrorEvent,
    FinalResultEvent,
)


async def stream_agent_start(request_id: str, agent_name: str):
    """Notify the frontend that an agent has started executing."""
    event = AgentStartEvent(
        agent=agent_name,
        message=f"{agent_name} started"
    )
    await ws_manager.send(request_id, event.model_dump())


async def stream_tool_call(
    request_id: str,
    agent_name: str,
    tool_name: str,
    data: Optional[Dict] = None
):
    """Notify the frontend that an agent is calling a tool."""
    event = ToolCallEvent(
        agent=agent_name,
        message=f"Calling tool: {tool_name}",
        data=data or {}
    )
    await ws_manager.send(request_id, event.model_dump())


async def stream_agent_complete(
    request_id: str,
    agent_name: str,
    data: Optional[Dict] = None
):
    """Notify the frontend that an agent has finished and share its output."""
    event = AgentCompleteEvent(
        agent=agent_name,
        message=f"{agent_name} completed",
        data=data or {}
    )
    await ws_manager.send(request_id, event.model_dump())


async def stream_error(
    request_id: str,
    agent_name: str,
    error_message: str
):
    """Stream an error event to the frontend."""
    event = ErrorEvent(
        agent=agent_name,
        message=error_message
    )
    await ws_manager.send(request_id, event.model_dump())


async def stream_final_result(
    request_id: str,
    decision: Dict,
    final_report: str
):
    """Stream the completed decision and full executive report to the frontend."""
    event = FinalResultEvent(
        message="Decision completed",
        data={
            "decision": decision,
            "final_report": final_report
        }
    )
    await ws_manager.send(request_id, event.model_dump())
