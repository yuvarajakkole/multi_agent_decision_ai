AGENT_WEIGHTS = {"market_agent":0.30,"financial_agent":0.35,"knowledge_agent":0.20,"strategy_agent":0.15}
THRESHOLD = 0.50

def compute_weighted_confidence(envelopes: dict) -> dict:
    per, w_sum, w_total, unreliable = {}, 0.0, 0.0, []
    for name, weight in AGENT_WEIGHTS.items():
        env  = envelopes.get(name, {})
        conf = env.get("confidence", 0.5)
        ok   = conf >= THRESHOLD
        per[name] = {"confidence":conf,"weight":weight,"contribution":round(conf*weight,4),
                     "is_reliable":ok,"errors":env.get("errors",[]),"source":env.get("source","unknown")}
        w_sum+=conf*weight; w_total+=weight
        if not ok: unreliable.append(name)
    wc      = round(w_sum/w_total, 3) if w_total else 0.0
    overall = wc >= THRESHOLD and len(unreliable) <= 1
    return {"weighted_confidence":wc,"per_agent":per,"unreliable_agents":unreliable,
            "overall_reliable":overall,"confidence_label":_lbl(wc)}

def adjust_decision_score(raw, mc, fc, kc) -> float:
    denom  = AGENT_WEIGHTS["market_agent"]+AGENT_WEIGHTS["financial_agent"]+AGENT_WEIGHTS["knowledge_agent"]
    avg    = (mc*AGENT_WEIGHTS["market_agent"]+fc*AGENT_WEIGHTS["financial_agent"]+kc*AGENT_WEIGHTS["knowledge_agent"])/denom
    return round(min(100, max(0, raw*(0.40+0.60*avg))), 1)

def _lbl(c):
    if c>=0.85: return "High"
    if c>=0.65: return "Medium"
    if c>=0.45: return "Low"
    return "Very Low"
