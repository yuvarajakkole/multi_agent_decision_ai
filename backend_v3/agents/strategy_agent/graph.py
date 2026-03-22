import json, re
from agents.strategy_agent.agent import run_strategy_agent
from core.reliability.confidence import adjust_decision_score
from core.reliability.validator import validate_agent_output
from core.trace.decision_trace import compact_output
from streaming.agent_step_streamer import stream_agent_start, stream_agent_complete

_FB={"decision":"WAIT","confidence_score":30,"total_score":30,"rationale":["Insufficient data"],
    "key_risks":["Data quality"],"conditions":[],"next_steps":["Manual review required"],
    "summary":"Automated analysis inconclusive."}

def _parse(raw):
    try: return json.loads(raw.strip().replace("```json","").replace("```","").strip())
    except: pass
    m=re.search(r"\{.*\}",raw,re.DOTALL)
    if m:
        try: return json.loads(m.group())
        except: pass
    return _FB.copy()

async def strategy_agent_node(state: dict) -> dict:
    print("\n========== STRATEGY AGENT NODE START ==========")
    rid=state["request_id"]; uq=state["user_query"]; market=state.get("market","unknown")
    trace=state.get("_trace")
    mc=state.get("_market_agent_envelope",{}).get("confidence",0.7)
    fc=state.get("_financial_agent_envelope",{}).get("confidence",0.7)
    kc=state.get("_knowledge_agent_envelope",{}).get("confidence",0.7)
    if trace: trace.start_step("strategy_agent")
    await stream_agent_start(rid,"strategy_agent")

    raw=await run_strategy_agent(uq,market,
        state.get("market_insights",{}),state.get("financial_analysis",{}),
        state.get("knowledge_summary",{}),mc,fc,kc)
    decision=_parse(raw)

    # Apply confidence weighting
    raw_score=float(decision.get("total_score",50))
    adj_score=adjust_decision_score(raw_score,mc,fc,kc)
    decision["total_score"]=adj_score
    decision["raw_score_before_confidence_adj"]=raw_score
    decision["agent_confidences"]={"market":mc,"financial":fc,"knowledge":kc}

    # Re-derive decision from adjusted score (strict thresholds)
    if adj_score>=68:    final="GO"
    elif adj_score>=50:  final="GO_WITH_CONDITIONS"
    elif adj_score>=33:  final="WAIT"
    else:                final="NO_GO"
    decision["decision"]=final

    # Warn if confidence forced a downgrade
    if abs(adj_score-raw_score)>5:
        decision["rationale"]=decision.get("rationale",[])+[
            f"Note: Raw score {raw_score} adjusted to {adj_score} due to data confidence levels."]

    envelope=validate_agent_output("strategy_agent","strategy_decision",decision,"llm")
    print(f"Strategy: {final} | Raw:{raw_score} → Adj:{adj_score} | Conf:{envelope['confidence']}")

    if trace: trace.log_step("strategy_agent",
        {"mc":mc,"fc":fc,"kc":kc,"raw_score":raw_score},compact_output(decision),
        envelope["confidence"],"llm",envelope["errors"],envelope["warnings"])
    await stream_agent_complete(rid,"strategy_agent",{
        "decision":final,"score":adj_score,"confidence":envelope["confidence"]})
    print("========== STRATEGY AGENT NODE END ==========\n")
    return {"strategy_decision":decision,"_strategy_agent_envelope":envelope}
