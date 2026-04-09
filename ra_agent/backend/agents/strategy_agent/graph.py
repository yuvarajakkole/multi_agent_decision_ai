"""
agents/strategy_agent/graph.py

Fixes:
  1. Ignores agents where confidence < IGNORE_THRESHOLD — uses only reliable data
  2. Score-based decision is final — LLM only provides explanation
  3. Invalid scores (None, out-of-range) → 0, marked in log
  4. Component scores always sum to total — no math errors
  5. Hard overrides checked before LLM call
"""

import json
import re
from datetime import datetime, timezone

from agents.strategy_agent.agent import run as run_strategy
from config.settings import MAX_AGENT_RETRIES, MIN_CONFIDENCE
from core.reliability.confidence import (
    compute_overall_confidence,
    IGNORE_THRESHOLD,
)
from streaming.streamer import stream_event


# ─── Score rubric ──────────────────────────────────────────────────────────────
# Market:    0–40
# Financial: 0–40
# Strategic: 0–20
# Total:     0–100

def _score_to_decision(score: float) -> str:
    if score >= 68:   return "GO"
    if score >= 50:   return "GO_WITH_CONDITIONS"
    if score >= 33:   return "WAIT"
    return "NO_GO"


def _parse(raw: str) -> tuple[dict, str]:
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
        "decision":       "WAIT",
        "adjusted_score": 30,
        "rationale":      ["Parse failed — insufficient data for decision"],
        "key_risks":      ["Data quality too low for reliable analysis"],
        "next_steps":     ["Improve data collection quality"],
        "summary":        "Decision deferred — data quality insufficient.",
        "_parse_error":   True,
    }, "fallback"


def _sanitise_score(value, label: str, warnings: list[str]) -> float:
    """Return a clean 0.0–100.0 float or 0 if invalid. Log every sanitisation."""
    if value is None:
        warnings.append(f"[INVALID_SCORE] {label}=None → set 0")
        return 0.0
    try:
        f = float(value)
    except (TypeError, ValueError):
        warnings.append(f"[INVALID_SCORE] {label}={value!r} not numeric → set 0")
        return 0.0
    if f < 0 or f > 100:
        warnings.append(f"[INVALID_SCORE] {label}={f} out of range → clamped")
        return max(0.0, min(100.0, f))
    return f


def _enforce_score_decision(data: dict, warnings: list[str]) -> dict:
    """
    Re-derive decision from score.  Code wins — LLM only provides explanation.
    Component scores must add up correctly.
    """
    mc = _sanitise_score(data.get("market_component"),    "market_component",    warnings)
    fc = _sanitise_score(data.get("financial_component"), "financial_component", warnings)
    sc = _sanitise_score(data.get("strategic_component"), "strategic_component", warnings)

    # Clamp to rubric maximums
    mc = min(mc, 40.0)
    fc = min(fc, 40.0)
    sc = min(sc, 20.0)

    total = round(mc + fc + sc, 2)

    # Override adjusted_score with sum of components (no floating arithmetic issues)
    data["market_component"]    = mc
    data["financial_component"] = fc
    data["strategic_component"] = sc
    data["adjusted_score"]      = total

    correct_decision = _score_to_decision(total)
    llm_decision     = data.get("decision", "")

    if llm_decision != correct_decision:
        data["_decision_overridden"]     = True
        data["_original_llm_decision"]   = llm_decision
        data.setdefault("rationale", []).append(
            f"[OVERRIDE] Score {total:.1f} → {correct_decision} "
            f"(LLM said '{llm_decision}', score-based decision enforced)"
        )
        warnings.append(
            f"[DECISION_OVERRIDE] LLM={llm_decision} overridden to {correct_decision} (score={total:.1f})"
        )

    data["decision"] = correct_decision
    return data


def _check_hard_overrides(
    market: dict,
    financial: dict,
    knowledge: dict,
) -> tuple[str | None, str]:
    """Hard rules that force NO_GO regardless of score."""
    inflation = market.get("inflation_pct") or financial.get("inflation_pct")
    if inflation and float(inflation) > 30:
        return "NO_GO", f"Inflation {inflation}% > 30% — real returns destroyed"

    irr = financial.get("estimated_irr_pct")
    if irr is not None and float(irr) < -20:
        return "NO_GO", f"IRR {irr}% deeply negative — project destroys value"

    budget_ok = knowledge.get("budget_within_policy", True)
    risk      = financial.get("risk_level", "Medium")
    if not budget_ok and risk == "Very High":
        return "NO_GO", "Budget exceeds policy AND risk=Very High"

    return None, ""


def _assess_strategy_quality(data: dict) -> tuple[float, list[str]]:
    issues     = []
    confidence = 1.0

    if data.get("_parse_error"):
        issues.append("[PARSE_ERROR] Strategy output parse failed")
        confidence -= 0.40

    if not data.get("rationale") or len(data.get("rationale", [])) == 0:
        issues.append("[MISSING] No rationale provided")
        confidence -= 0.15

    if not data.get("key_risks"):
        issues.append("[MISSING] No risks identified")
        confidence -= 0.08

    score = data.get("adjusted_score")
    if score is None or not (0 <= float(score) <= 100):
        issues.append(f"[INVALID_SCORE] adjusted_score={score}")
        confidence -= 0.10

    return round(max(0.0, min(1.0, confidence)), 3), issues


async def strategy_agent_node(state: dict) -> dict:
    rid     = state["request_id"]
    retries = int(state.get("strategy_retries", 0))

    mc = float(state.get("market_confidence",    0.0))
    fc = float(state.get("financial_confidence", 0.0))
    kc = float(state.get("knowledge_confidence", 0.0))

    mig = state.get("quality_flags", {}).get("market_ignore",    mc < IGNORE_THRESHOLD)
    fig = state.get("quality_flags", {}).get("financial_ignore", fc < IGNORE_THRESHOLD)
    kig = state.get("quality_flags", {}).get("knowledge_ignore", kc < IGNORE_THRESHOLD)

    # If all agents unreliable, defer
    all_ignored = mig and fig and kig
    if all_ignored and retries == 0:
        reason = (
            f"All agents below confidence threshold "
            f"(market={mc:.2f}, financial={fc:.2f}, knowledge={kc:.2f})"
        )
        print(f"[strategy_agent] ALL AGENTS IGNORED — {reason}")
        return {
            "strategy_decision": {
                "decision":          "WAIT",
                "adjusted_score":    20,
                "market_component":  0,
                "financial_component": 0,
                "strategic_component": 0,
                "rationale":         [f"[DEFERRED] {reason}"],
                "key_risks":         ["Cannot make reliable decision with current data quality"],
                "next_steps":        ["Retry with better data sources"],
                "summary":           "Decision deferred — all agent data below reliability threshold.",
                "_deferred":         True,
            },
            "strategy_confidence": 0.15,
            "strategy_retries":    1,
            "routing_decision":    "low_quality_defer",
            "execution_log": [{
                "agent":     "strategy_agent",
                "action":    "deferred_all_ignored",
                "reason":    reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }],
        }

    await stream_event(rid, "agent_start", "strategy_agent",
                       f"Synthesising decision (attempt {retries + 1})")
    print(
        f"\n[strategy_agent] START  mc={mc:.3f}(ignore={mig})  "
        f"fc={fc:.3f}(ignore={fig})  kc={kc:.3f}(ignore={kig})  retry={retries}"
    )

    # Only pass reliable agent data to strategy
    market_data    = {} if mig else state.get("market_insights",    {})
    financial_data = {} if fig else state.get("financial_analysis", {})
    knowledge_data = {} if kig else state.get("knowledge_summary",  {})

    ignored_agents = [n for n, ig in [("market", mig), ("financial", fig), ("knowledge", kig)] if ig]
    if ignored_agents:
        print(f"[strategy_agent] Ignoring unreliable agents: {ignored_agents}")

    # Hard overrides checked before LLM call
    override_decision, override_reason = _check_hard_overrides(
        market_data, financial_data, knowledge_data
    )
    if override_decision:
        print(f"[strategy_agent] HARD OVERRIDE: {override_reason}")
        decision_data = {
            "decision":             "NO_GO",
            "adjusted_score":       10,
            "market_component":     0,
            "financial_component":  0,
            "strategic_component":  0,
            "rationale":            [f"[HARD_OVERRIDE] {override_reason}"],
            "key_risks":            ["Fundamental constraint — not addressable"],
            "conditions":           [],
            "blocking_issues":      [override_reason],
            "next_steps":           ["Do not proceed"],
            "summary":              f"Hard NO_GO: {override_reason}",
            "_hard_override":       True,
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
                "agent":     "strategy_agent",
                "action":    "hard_override",
                "decision":  "NO_GO",
                "reason":    override_reason,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }],
        }

    prev_decision = None
    retry_issues  = None
    if retries > 0:
        prev_data     = state.get("strategy_decision", {})
        prev_decision = json.dumps(prev_data)
        retry_issues  = state.get("quality_flags", {}).get("strategy_issues", [])

    raw = await run_strategy(
        user_query           = state["user_query"],
        market               = state.get("market", ""),
        budget               = float(state.get("budget", 0)),
        timeline_months      = int(state.get("timeline_months", 12)),
        market_insights      = market_data,
        financial_analysis   = financial_data,
        knowledge_summary    = knowledge_data,
        market_confidence    = mc,
        financial_confidence = fc,
        knowledge_confidence = kc,
        ignored_agents       = ignored_agents,
        quality_flags        = state.get("quality_flags", {}),
        previous_decision    = prev_decision,
        retry_issues         = retry_issues,
    )

    data, _parse_method = _parse(raw)

    # Enforce score-based decision — LLM cannot override
    score_warnings: list[str] = []
    data = _enforce_score_decision(data, score_warnings)

    confidence, issues = _assess_strategy_quality(data)
    needs_retry = (
        confidence < MIN_CONFIDENCE
        and retries < MAX_AGENT_RETRIES
    )

    all_issues = issues + score_warnings
    print(
        f"[strategy_agent] {data['decision']}  "
        f"score={data.get('adjusted_score')}  "
        f"components=market:{data.get('market_component')}"
        f"+financial:{data.get('financial_component')}"
        f"+strategic:{data.get('strategic_component')}"
        f"  conf={confidence}"
    )

    log_entry = {
        "agent":             "strategy_agent",
        "timestamp":         datetime.now(timezone.utc).isoformat(),
        "attempt":           retries + 1,
        "decision":          data["decision"],
        "score":             data.get("adjusted_score"),
        "market_component":  data.get("market_component"),
        "financial_component": data.get("financial_component"),
        "strategic_component": data.get("strategic_component"),
        "confidence":        confidence,
        "overridden":        data.get("_decision_overridden", False),
        "ignored_agents":    ignored_agents,
        "issues":            all_issues,
        "will_retry":        needs_retry,
    }

    await stream_event(rid, "agent_complete", "strategy_agent", {
        "decision":       data["decision"],
        "score":          data.get("adjusted_score"),
        "confidence":     confidence,
        "ignored_agents": ignored_agents,
        "needs_retry":    needs_retry,
    })

    return {
        "strategy_decision":  data,
        "strategy_confidence": confidence,
        "strategy_retries":   retries + 1,
        "quality_flags": {
            "strategy_issues":      all_issues,
            "strategy_needs_retry": needs_retry,
        },
        "routing_decision": "complete" if not needs_retry else "strategy_retry",
        "execution_log": [log_entry],
    }
