"""
agents/communication_agent/graph.py

Fixed:
  1. Uses compute_overall_confidence from confidence.py (single source of truth)
  2. Confidence from state — never recalculated from scratch here
  3. Budget=0 handled gracefully (not defaulted to 1_000_000)
"""

from datetime import datetime, timezone
from agents.communication_agent.agent import run as run_comms
from core.reliability.confidence import compute_overall_confidence
from streaming.streamer import stream_event, stream_final


async def communication_agent_node(state: dict) -> dict:
    rid = state["request_id"]
    await stream_event(rid, "agent_start", "communication_agent", "Generating report")
    print("\n[communication_agent] START")

    # Pull per-agent confidences from state
    mc = float(state.get("market_confidence",    0.0) or 0.0)
    fc = float(state.get("financial_confidence", 0.0) or 0.0)
    kc = float(state.get("knowledge_confidence", 0.0) or 0.0)

    # Source labels from quality flags (set by agent graphs)
    def _src(flags_key: str, default: str) -> str:
        flags = state.get("quality_flags", {})
        # Check if agent was ignored — that tells us source was unreliable
        if flags.get(f"{flags_key}_ignore"):
            return "unknown"
        return default

    # Reuse confidence calculation from confidence.py — same formula everywhere
    conf_report = compute_overall_confidence(
        market_conf    = mc,
        financial_conf = fc,
        knowledge_conf = kc,
        market_source    = _src("market",    "partial_live"),
        financial_source = _src("financial", "partial_live"),
        knowledge_source = "static",   # knowledge always reads from JSON file
        learning_adj  = float(state.get("_confidence_adj", 0.0)),
    )

    wc         = conf_report["weighted_confidence"]
    conf_label = conf_report["label"]

    # Budget: use 0 if not specified — do not substitute defaults
    budget = float(state.get("budget", 0) or 0)

    report = await run_comms(
        strategy_decision   = state.get("strategy_decision", {}),
        market_insights     = state.get("market_insights",   {}),
        financial_analysis  = state.get("financial_analysis",{}),
        knowledge_summary   = state.get("knowledge_summary", {}),
        user_query          = state["user_query"],
        market              = state.get("market", ""),
        budget              = budget,
        timeline_months     = int(state.get("timeline_months", 12) or 12),
        weighted_confidence = wc,
    )

    sd = state.get("strategy_decision", {})

    log_entry = {
        "agent":       "communication_agent",
        "timestamp":   datetime.now(timezone.utc).isoformat(),
        "action":      "report_generated",
        "chars":       len(report),
        "decision":    sd.get("decision"),
        "confidence":  wc,
        "conf_label":  conf_label,
    }

    await stream_event(rid, "agent_complete", "communication_agent",
                       {"chars": len(report), "decision": sd.get("decision"),
                        "confidence": wc, "label": conf_label})
    await stream_final(rid, sd, report, wc, conf_label)

    print(f"[communication_agent] END  decision={sd.get('decision')}  "
          f"conf={wc}({conf_label})  chars={len(report)}")

    return {
        "final_report":       report,
        "weighted_confidence": wc,
        "confidence_label":   conf_label,
        "decision_is_final":  True,
        "execution_log":      [log_entry],
    }
