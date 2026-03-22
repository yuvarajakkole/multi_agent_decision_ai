from typing import Optional, Dict
from streaming.websocket_manager import ws_manager
from streaming.event_models import AgentStartEvent,AgentCompleteEvent,ErrorEvent,FinalResultEvent

async def stream_agent_start(rid,agent):
    await ws_manager.send(rid,AgentStartEvent(agent=agent,message=f"{agent} started").model_dump())
async def stream_agent_complete(rid,agent,data=None):
    await ws_manager.send(rid,AgentCompleteEvent(agent=agent,message=f"{agent} completed",data=data or {}).model_dump())
async def stream_error(rid,agent,msg):
    await ws_manager.send(rid,ErrorEvent(agent=agent,message=msg).model_dump())
async def stream_final_result(rid,decision,report):
    await ws_manager.send(rid,FinalResultEvent(message="Done",data={"decision":decision,"final_report":report}).model_dump())
