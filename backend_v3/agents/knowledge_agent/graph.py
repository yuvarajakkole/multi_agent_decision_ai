import json, re
from agents.knowledge_agent.agent import run_knowledge_agent
from core.reliability.validator import validate_agent_output
from core.trace.decision_trace import compact_input, compact_output
from streaming.agent_step_streamer import stream_agent_start, stream_agent_complete

_FB={"company_name":"RA Groups","strategic_fit":"Medium","available_budget_usd":3_000_000,
    "budget_within_limits":True,"max_allowed_investment_usd":5_000_000,
    "risk_appetite_match":"Aligned","company_strengths":[],"company_weaknesses":[],
    "relevant_past_expansions":[],"has_past_experience_in_this_market":False,
    "summary":"Knowledge data unavailable."}

def _parse(raw):
    try: return json.loads(raw.strip().replace("```json","").replace("```","").strip()),"hybrid"
    except: pass
    m=re.search(r"\{.*\}",raw,re.DOTALL)
    if m:
        try: return json.loads(m.group()),"hybrid"
        except: pass
    return _FB.copy(),"fallback"

async def knowledge_agent_node(state: dict) -> dict:
    print("\n========== KNOWLEDGE AGENT NODE START ==========")
    rid=state["request_id"]; trace=state.get("_trace")
    if trace: trace.start_step("knowledge_agent")
    await stream_agent_start(rid,"knowledge_agent")
    raw=await run_knowledge_agent(
        f"Query: {state['user_query']}\nMarket: {state.get('market','unknown')}\n"
        f"Budget: ${state.get('budget',0):,.0f}\nTimeline: {state.get('timeline_months',12)} months")
    data, source=_parse(raw)
    envelope=validate_agent_output("knowledge_agent","knowledge_summary",data,source)
    print(f"Knowledge confidence: {envelope['confidence']} | Fit:{data.get('strategic_fit')} | Errors:{envelope['errors']}")
    if trace: trace.log_step("knowledge_agent",compact_input(state),compact_output(data),
        envelope["confidence"],source,envelope["errors"],envelope["warnings"])
    await stream_agent_complete(rid,"knowledge_agent",{
        "strategic_fit":data.get("strategic_fit"),"past_experience":data.get("has_past_experience_in_this_market"),
        "confidence":envelope["confidence"]})
    print("========== KNOWLEDGE AGENT NODE END ==========\n")
    return {"knowledge_summary":data,"_knowledge_agent_envelope":envelope}
