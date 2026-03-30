"""
agents/strategy_agent/graph.py

Strategy agent node.  This is the ONLY node that reads from all three
parallel research agents and makes the final GO/NO_GO decision.

Critical behaviour:
- Verifies the LLM's score arithmetic against the rubric.
- If the LLM's decision contradicts the calculated score, code wins.
- If data quality is too poor, routes back to the research agents.
- Writes routing signals so the graph can decide what to do next.
"""

import json
import re
from datetime import datetime, timezone

from agents.strategy_agent.agent import run as run_strategy
from config.settings import MAX_AGENT_RETRIES, MIN_CONFIDENCE
from streaming.streamer import stream_event


def _parse(raw: str) -> tuple:
    cleaned = raw.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned), "direct"
    except Exception:
        pass
    m = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if m:
        try:
            return json.loads(m.group()), "regex"
        except Exception:
            pass
    return {
        "decision": "WAIT",
        "adjusted_score": 40,
        "confidence_pct": 30,
        "rationale": ["Analysis failed — insufficient data"],
        "key_risks": ["Data quality too low for reliable decision"],
        "next_steps": ["Collect better market and financial data"],
        "summary": "Decision deferred — data quality insufficient.",
        "_parse_error": True,
    }, "fallback"


def _verify_and_enforce_decision(data: dict) -> dict:
    """
    Independently re-derive the decision from the adjusted_score.
    If the LLM's decision contradicts the score, code overrides it.
    This prevents the LLM from ignoring the rubric.
    """
    score = float(data.get("adjusted_score", 40))

    if score >= 68:    correct = "GO"
    elif score >= 50:  correct = "GO_WITH_CONDITIONS"
    elif score >= 33:  correct = "WAIT"
    else:              correct = "NO_GO"

    llm_decision = data.get("decision", "")
    if llm_decision != correct:
        data["_decision_overridden"] = True
        data["_original_llm_decision"] = llm_decision
        data["decision"] = correct
        override_note = f"Score {score:.1f} → {correct} (LLM said {llm_decision}, code overrides)"
        data.setdefault("rationale", []).append(override_note)

    return data


def _check_hard_overrides(market_insights: dict, financial_analysis: dict,
                           knowledge_summary: dict) -> str | None:
    """
    Hard override rules that force NO_GO or WAIT regardless of score.
    Returns override reason or None.
    """
    inflation = market_insights.get("inflation_pct") or financial_analysis.get("inflation_pct")
    if inflation and float(inflation) > 30:
        return f"NO_GO override: inflation {inflation}% > 30% — real returns destroyed"

    irr = financial_analysis.get("estimated_irr_pct")
    if irr is not None and float(irr) < -20:
        return f"NO_GO override: IRR {irr}% deeply negative — project destroys value"

    budget_ok = knowledge_summary.get("budget_within_policy", True)
    risk      = financial_analysis.get("risk_level", "Medium")
    if not budget_ok and risk == "Very High":
        return "NO_GO override: budget exceeds policy AND risk is Very High"

    return None


def _assess_quality(data: dict) -> tuple:
    issues     = []
    confidence = 1.0

    if data.get("_parse_error"):
        issues.append("Parse failed")
        confidence -= 0.40

    decision = data.get("decision", "")
    if decision not in ("GO", "GO_WITH_CONDITIONS", "WAIT", "NO_GO"):
        issues.append(f"Invalid decision: '{decision}'")
        confidence -= 0.30

    if not data.get("rationale") or len(data.get("rationale", [])) == 0:
        issues.append("No rationale provided")
        confidence -= 0.15

    score = data.get("adjusted_score")
    if score is None:
        issues.append("adjusted_score missing")
        confidence -= 0.10

    return round(max(0.0, min(1.0, confidence)), 3), issues


async def strategy_agent_node(state: dict) -> dict:
    rid      = state["request_id"]
    retries  = int(state.get("strategy_retries", 0))

    # Pull agent confidences
    mc = float(state.get("market_confidence",    0.7))
    fc = float(state.get("financial_confidence", 0.7))
    kc = float(state.get("knowledge_confidence", 0.7))

    # If all upstream agents have poor data, defer decision
    avg_conf = mc * 0.35 + fc * 0.35 + kc * 0.30
    if avg_conf < 0.45 and retries == 0:
        print(f"[strategy_agent] avg_confidence={avg_conf:.2f} too low — deferring")
        return {
            "strategy_decision": {
                "decision":       "WAIT",
                "adjusted_score": 30,
                "confidence_pct": 20,
                "rationale":      ["Data quality insufficient across all agents — cannot make reliable decision"],
                "key_risks":      ["All agent confidence scores below threshold"],
                "next_steps":     ["Retry data collection with improved queries"],
                "summary":        "Decision deferred: upstream data quality too low for reliable analysis.",
                "_deferred":      True,
            },
            "strategy_confidence": 0.2,
            "strategy_retries":    1,
            "routing_decision":    "low_quality_defer",
            "execution_log": [{
                "agent": "strategy_agent", "action": "deferred",
                "reason": f"avg_confidence={avg_conf:.2f} < 0.45",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }],
        }

    await stream_event(rid, "agent_start", "strategy_agent",
                       f"Synthesising decision (attempt {retries + 1})")
    print(f"\n[strategy_agent] START  mc={mc}  fc={fc}  kc={kc}  retry={retries}")

    market_insights    = state.get("market_insights",    {})
    financial_analysis = state.get("financial_analysis", {})
    knowledge_summary  = state.get("knowledge_summary",  {})

    # Check hard overrides before calling LLM
    override_reason = _check_hard_overrides(
        market_insights, financial_analysis, knowledge_summary
    )
    if override_reason:
        print(f"[strategy_agent] HARD OVERRIDE: {override_reason}")
        decision_data = {
            "decision":       "NO_GO",
            "adjusted_score": 15,
            "confidence_pct": 95,
            "rationale":      [override_reason],
            "key_risks":      ["Hard policy constraint triggered"],
            "conditions":     [],
            "blocking_issues": [override_reason],
            "next_steps":     ["Do not proceed — fundamental constraint not addressable"],
            "summary":        f"Hard NO_GO: {override_reason}",
            "_hard_override": True,
        }
        await stream_event(rid, "agent_complete", "strategy_agent", {
            "decision": "NO_GO", "reason": "hard_override", "override": override_reason
        })
        return {
            "strategy_decision":  decision_data,
            "strategy_confidence": 0.95,
            "strategy_retries":   retries + 1,
            "routing_decision":   "complete",
            "execution_log": [{
                "agent": "strategy_agent", "action": "hard_override",
                "decision": "NO_GO", "reason": override_reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }],
        }

    # Get previous decision if retry
    prev_decision = None
    retry_issues  = None
    if retries > 0:
        prev_data     = state.get("strategy_decision", {})
        prev_decision = json.dumps(prev_data)
        retry_issues  = state.get("quality_flags", {}).get("strategy_issues", [])

    raw = await run_strategy(
        user_query           = state["user_query"],
        market               = state.get("market", ""),
        budget               = float(state.get("budget", 1_000_000)),
        timeline_months      = int(state.get("timeline_months", 12)),
        market_insights      = market_insights,
        financial_analysis   = financial_analysis,
        knowledge_summary    = knowledge_summary,
        market_confidence    = mc,
        financial_confidence = fc,
        knowledge_confidence = kc,
        quality_flags        = state.get("quality_flags", {}),
        previous_decision    = prev_decision,
        retry_issues         = retry_issues,
    )

    data, _parse_method = _parse(raw)

    # Code enforces decision based on score
    data = _verify_and_enforce_decision(data)

    confidence, issues = _assess_quality(data)
    needs_retry = (
        confidence < MIN_CONFIDENCE
        and retries < MAX_AGENT_RETRIES
    )

    print(f"[strategy_agent] {data['decision']}  "
          f"score={data.get('adjusted_score')}  conf={confidence}")

    log_entry = {
        "agent":       "strategy_agent",
        "timestamp":   datetime.now(timezone.utc).isoformat(),
        "attempt":     retries + 1,
        "decision":    data["decision"],
        "score":       data.get("adjusted_score"),
        "confidence":  confidence,
        "overridden":  data.get("_decision_overridden", False),
        "issues":      issues,
        "will_retry":  needs_retry,
    }

    await stream_event(rid, "agent_complete", "strategy_agent", {
        "decision":    data["decision"],
        "score":       data.get("adjusted_score"),
        "confidence":  confidence,
        "needs_retry": needs_retry,
    })

    return {
        "strategy_decision":  data,
        "strategy_confidence": confidence,
        "strategy_retries":   retries + 1,
        "quality_flags": {
            "strategy_issues":     issues,
            "strategy_needs_retry": needs_retry,
        },
        "routing_decision": "complete" if not needs_retry else "strategy_retry",
        "execution_log": [log_entry],
    }
