"""agents/communication_agent/graph.py — Final report node."""

from datetime import datetime, timezone
from agents.communication_agent.agent import run as run_comms
from streaming.streamer import stream_event, stream_final


async def communication_agent_node(state: dict) -> dict:
    rid = state["request_id"]
    await stream_event(rid, "agent_start", "communication_agent", "Generating report")
    print("\n[communication_agent] START")

    # Compute real weighted confidence from agent scores
    mc = float(state.get("market_confidence",    0.0))
    fc = float(state.get("financial_confidence", 0.0))
    kc = float(state.get("knowledge_confidence", 0.0))
    wc = round(mc * 0.35 + fc * 0.35 + kc * 0.30, 3)
    wc = max(0.0, min(1.0, wc))
    conf_label = "High" if wc >= 0.80 else "Medium" if wc >= 0.60 else "Low"

    report = await run_comms(
        strategy_decision    = state.get("strategy_decision", {}),
        market_insights      = state.get("market_insights", {}),
        financial_analysis   = state.get("financial_analysis", {}),
        knowledge_summary    = state.get("knowledge_summary", {}),
        user_query           = state["user_query"],
        market               = state.get("market", ""),
        budget               = float(state.get("budget", 1_000_000)),
        timeline_months      = int(state.get("timeline_months", 12)),
        weighted_confidence  = wc,
    )

    sd = state.get("strategy_decision", {})

    log_entry = {
        "agent":       "communication_agent",
        "timestamp":   datetime.now(timezone.utc).isoformat(),
        "action":      "report_generated",
        "chars":       len(report),
        "decision":    sd.get("decision"),
        "confidence":  wc,
    }

    await stream_event(rid, "agent_complete", "communication_agent",
                       {"chars": len(report), "decision": sd.get("decision")})
    await stream_final(rid, sd, report, wc, conf_label)

    print(f"[communication_agent] END  chars={len(report)}  "
          f"decision={sd.get('decision')}  confidence={wc}")
    return {
        "final_report":       report,
        "weighted_confidence": wc,
        "confidence_label":   conf_label,
        "decision_is_final":  True,
        "execution_log":      [log_entry],
    }
