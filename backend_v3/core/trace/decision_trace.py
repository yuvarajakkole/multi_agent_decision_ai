import time
from datetime import datetime, timezone

class DecisionTrace:
    def __init__(self, request_id, user_query, market):
        self.request_id=request_id; self.started_at=datetime.now(timezone.utc).isoformat()
        self.user_query=user_query; self.market=market; self.steps=[]; self._t={}
    def start_step(self, agent): self._t[agent]=time.monotonic()
    def log_step(self, agent, inp, out, confidence, source, errors, warnings):
        el=round(time.monotonic()-self._t.get(agent,time.monotonic()),3)
        self.steps.append({"step":len(self.steps)+1,"agent":agent,
            "timestamp":datetime.now(timezone.utc).isoformat(),"duration_sec":el,
            "input_summary":inp,"output_summary":out,"confidence":confidence,
            "source":source,"errors":errors,"warnings":warnings,
            "status":"ok" if not errors else "degraded"})
    def to_dict(self):
        return {"request_id":self.request_id,"user_query":self.user_query,"market":self.market,
            "started_at":self.started_at,"ended_at":datetime.now(timezone.utc).isoformat(),
            "total_steps":len(self.steps),"steps":self.steps}

def compact_input(state):
    return {k:state.get(k) for k in ("user_query","market","budget","timeline_months")}
def compact_output(data, n=6):
    if not isinstance(data,dict): return {}
    return {k:data[k] for k in list(data.keys())[:n]}
