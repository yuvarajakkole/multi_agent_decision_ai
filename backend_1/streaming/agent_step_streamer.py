import asyncio
from typing import Optional, Dict

from .websocket_manager import ws_manager
from .event_models import (
    AgentStartEvent,
    AgentCompleteEvent,
    ToolCallEvent,
    ErrorEvent,
    FinalResultEvent
)


# ---------------------------------------------------------
# STREAM AGENT START
# ---------------------------------------------------------

async def stream_agent_start(request_id: str, agent_name: str):

    event = AgentStartEvent(

        agent=agent_name,

        message=f"{agent_name} started"

    )

    await ws_manager.send(request_id, event.dict())


# ---------------------------------------------------------
# STREAM TOOL CALL
# ---------------------------------------------------------

async def stream_tool_call(
    request_id: str,
    agent_name: str,
    tool_name: str,
    data: Optional[Dict] = None
):

    event = ToolCallEvent(

        agent=agent_name,

        message=f"Calling tool: {tool_name}",

        data=data or {}

    )

    await ws_manager.send(request_id, event.dict())


# ---------------------------------------------------------
# STREAM AGENT COMPLETE
# ---------------------------------------------------------

async def stream_agent_complete(
    request_id: str,
    agent_name: str,
    data: Optional[Dict] = None
):

    event = AgentCompleteEvent(

        agent=agent_name,

        message=f"{agent_name} completed",

        data=data or {}

    )

    await ws_manager.send(request_id, event.dict())


# ---------------------------------------------------------
# STREAM ERROR
# ---------------------------------------------------------

async def stream_error(
    request_id: str,
    agent_name: str,
    error_message: str
):

    event = ErrorEvent(

        agent=agent_name,

        message=error_message

    )

    await ws_manager.send(request_id, event.dict())


# ---------------------------------------------------------
# STREAM FINAL RESULT
# ---------------------------------------------------------

async def stream_final_result(
    request_id: str,
    decision: Dict,
    final_report: str
):

    event = FinalResultEvent(

        message="Decision completed",

        data={
            "decision": decision,
            "final_report": final_report
        }

    )

    await ws_manager.send(request_id, event.dict())



# from typing import Dict, Any


# from backend.streaming.websocket_manager import websocket_manager
# from backend.streaming.event_models import (
#     AgentStartEvent,
#     AgentCompleteEvent,
#     AgentThinkingEvent,
#     ToolCallEvent,
#     FinalResultEvent
# )


# class AgentStepStreamer:
#     """
#     Streams agent execution steps to the UI.
#     """

#     async def agent_start(self, request_id: str, agent_name: str):
#         """
#         Notify UI that agent started execution.
#         """

#         event = AgentStartEvent(
#             agent=agent_name,
#             message=f"{agent_name} started"
#         )

#         await websocket_manager.send_event(
#             request_id,
#             event.dict()
#         )

#     async def agent_thinking(self, request_id: str, agent_name: str, message: str):
#         """
#         Send thinking update.
#         """

#         event = AgentThinkingEvent(
#             agent=agent_name,
#             message=message
#         )

#         await websocket_manager.send_event(
#             request_id,
#             event.dict()
#         )

#     async def tool_call(self, request_id: str, agent_name: str, tool_name: str):
#         """
#         Notify UI about tool usage.
#         """

#         event = ToolCallEvent(
#             agent=agent_name,
#             message=f"Using tool: {tool_name}"
#         )

#         await websocket_manager.send_event(
#             request_id,
#             event.dict()
#         )

#     async def agent_complete(self, request_id: str, agent_name: str, data: Dict[str, Any]):
#         """
#         Notify UI agent finished.
#         """

#         event = AgentCompleteEvent(
#             agent=agent_name,
#             message=f"{agent_name} finished",
#             data=data
#         )

#         await websocket_manager.send_event(
#             request_id,
#             event.dict()
#         )

#     async def final_result(self, request_id: str, result: Dict[str, Any]):
#         """
#         Send final decision.
#         """

#         event = FinalResultEvent(
#             data=result
#         )

#         await websocket_manager.send_event(
#             request_id,
#             event.dict()
#         )


# # Global instance
# agent_step_streamer = AgentStepStreamer()