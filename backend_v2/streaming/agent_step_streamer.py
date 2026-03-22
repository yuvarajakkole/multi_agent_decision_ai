from typing import Optional, Dict
from streaming.websocket_manager import ws_manager
from streaming.event_models import (
    AgentStartEvent, AgentCompleteEvent, ToolCallEvent,
    ErrorEvent, FinalResultEvent,
)

async def stream_agent_start(request_id: str, agent_name: str):
    await ws_manager.send(request_id,
        AgentStartEvent(agent=agent_name, message=f"{agent_name} started").model_dump())

async def stream_tool_call(request_id: str, agent_name: str,
                           tool_name: str, data: Optional[Dict] = None):
    await ws_manager.send(request_id,
        ToolCallEvent(agent=agent_name, message=f"Calling tool: {tool_name}",
                      data=data or {}).model_dump())

async def stream_agent_complete(request_id: str, agent_name: str,
                                data: Optional[Dict] = None):
    await ws_manager.send(request_id,
        AgentCompleteEvent(agent=agent_name, message=f"{agent_name} completed",
                           data=data or {}).model_dump())

async def stream_error(request_id: str, agent_name: str, error_message: str):
    await ws_manager.send(request_id,
        ErrorEvent(agent=agent_name, message=error_message).model_dump())

async def stream_final_result(request_id: str, decision: Dict, final_report: str):
    await ws_manager.send(request_id,
        FinalResultEvent(message="Decision completed",
                         data={"decision": decision, "final_report": final_report}).model_dump())
