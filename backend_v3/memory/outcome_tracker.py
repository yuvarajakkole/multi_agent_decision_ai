import json,threading
from pathlib import Path
from datetime import datetime,timezone
_PATH=Path(__file__).resolve().parent/"decision_history.json"
_lock=threading.Lock()
def _load():
    if _PATH.exists():
        try: return json.loads(_PATH.read_text())
        except: pass
    return []
def _save(d): _PATH.write_text(json.dumps(d,indent=2))
def save_decision(rid,uq,market,decision,confidence,score,agent_confs):
    with _lock:
        h=_load()
        h.append({"request_id":rid,"timestamp":datetime.now(timezone.utc).isoformat(),
            "user_query":uq,"market":market.lower(),"decision":decision,
            "confidence":confidence,"total_score":score,"agent_confidences":agent_confs,
            "actual_outcome":None,"outcome_notes":""})
        _save(h)
def compute_confidence_adjustment(market):
    with _lock: h=_load()
    cases=[c for c in h if c.get("market","").lower()==market.lower() and c.get("actual_outcome")]
    if not cases: return 0.0
    rate=sum(1 for c in cases if c["actual_outcome"]=="success")/len(cases)
    return +0.05 if rate>=0.8 else 0.0 if rate>=0.6 else -0.08 if rate>=0.4 else -0.15
def record_outcome(rid,outcome,notes=""):
    with _lock:
        h=_load()
        for e in h:
            if e.get("request_id")==rid: e["actual_outcome"]=outcome; e["outcome_notes"]=notes; break
        _save(h)
def get_history_summary():
    with _lock: h=_load()
    if not h: return {"total":0,"by_decision":{},"by_market":{}}
    by_d={};by_m={}
    for e in h:
        by_d[e.get("decision","?")]=by_d.get(e.get("decision","?"),0)+1
        by_m[e.get("market","?")]=by_m.get(e.get("market","?"),0)+1
    return {"total":len(h),"by_decision":by_d,"by_market":by_m,
        "avg_confidence":round(sum(e.get("confidence",0) for e in h)/len(h),3)}
