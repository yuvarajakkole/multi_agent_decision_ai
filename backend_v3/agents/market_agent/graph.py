import json, re
from agents.market_agent.agent import run_market_agent
from core.reliability.validator import validate_agent_output
from core.trace.decision_trace import compact_input, compact_output
from streaming.agent_step_streamer import stream_agent_start, stream_agent_complete

def _parse(raw, market):
    try: return json.loads(raw.strip().replace("```json","").replace("```","").strip()), "hybrid"
    except: pass
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try: return json.loads(m.group()), "hybrid"
        except: pass
    return {"market":market,"gdp_growth_percent":"N/A","inflation_percent":"N/A",
        "competition_level":"Medium","market_attractiveness":"Unknown",
        "market_attractiveness_score":50,"summary":"Market data unavailable."}, "fallback"

async def market_agent_node(state: dict) -> dict:
    print("\n========== MARKET AGENT NODE START ==========")
    request_id=state["request_id"]; market=state.get("market","unknown")
    trace=state.get("_trace")
    if trace: trace.start_step("market_agent")
    await stream_agent_start(request_id,"market_agent")
    raw = await run_market_agent(
        f"Analyse this SPECIFIC query — every answer must be unique to this product+market:\n"
        f"Query: {state['user_query']}\n"
        f"Target Market/Country: {market}\n"
        f"Budget: ${state.get('budget',0):,.0f}\n"
        f"Timeline: {state.get('timeline_months',12)} months\n\n"
        "Extract the exact product from the query. Use all tools. Return JSON.")
    data, source = _parse(raw, market)
    envelope = validate_agent_output("market_agent","market_insights",data,source)
    print(f"Market confidence: {envelope['confidence']} | Score: {data.get('market_attractiveness_score')} | Errors: {envelope['errors']}")
    if trace: trace.log_step("market_agent",compact_input(state),compact_output(data),
        envelope["confidence"],source,envelope["errors"],envelope["warnings"])
    await stream_agent_complete(request_id,"market_agent",{
        "attractiveness_score":data.get("market_attractiveness_score"),
        "go_no_go":data.get("go_no_go_signal"),"confidence":envelope["confidence"]})
    print("========== MARKET AGENT NODE END ==========\n")
    return {"market_insights":data,"_market_agent_envelope":envelope}
