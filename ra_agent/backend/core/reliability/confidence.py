"""
core/reliability/confidence.py

Single source of truth for confidence calculations.

KEY RULE: final confidence = MIN across retries.
This is enforced in each agent graph node, NOT here globally,
because we must skip the MIN rule on the first call (retries==0)
to avoid LangGraph's initial-state 0.0 coercion bug.
"""

import logging
from typing import Optional

log = logging.getLogger("confidence")

# Thresholds
IGNORE_THRESHOLD  = 0.40   # agents below this are excluded from weighted average
MIN_VIABLE        = 0.25   # floor when all agents ignored

# Source-based confidence bases
CONF_LIVE         = 1.00
CONF_PARTIAL_LIVE = 0.60
CONF_STATIC       = 0.30
CONF_UNKNOWN      = 0.00

# Agent weights
_AGENT_WEIGHTS = {
    "market_agent":    0.35,
    "financial_agent": 0.35,
    "knowledge_agent": 0.30,
}


def apply_source_penalty_to_confidence(current: float, source: str) -> float:
    """Apply source-based cap to confidence. Used in agent graph nodes."""
    if source == "unknown":
        return CONF_UNKNOWN
    if source == "static":
        return min(current, CONF_STATIC)
    if source in ("partial_live", "fallback"):
        return min(current, CONF_PARTIAL_LIVE)
    return current   # live_api — no cap


def min_confidence_across_retries(previous: Optional[float], current: float) -> float:
    """
    Enforce MIN rule across retries.
    IMPORTANT: caller must pass previous=None on first call (retries==0)
    to avoid the LangGraph initial-state 0.0 coercion problem.
    """
    if previous is None:
        return round(current, 4)
    result = round(min(previous, current), 4)
    if result < current:
        log.debug("[confidence] MIN rule: %.3f → %.3f (kept lower)", current, result)
    return result


def compute_overall_confidence(
    market_conf:     float,
    financial_conf:  float,
    knowledge_conf:  float,
    market_source:     str   = "unknown",
    financial_source:  str   = "unknown",
    knowledge_source:  str   = "unknown",
    learning_adj: float = 0.0,
) -> dict:
    """
    Compute final weighted confidence across all agents.
    Agents below IGNORE_THRESHOLD get weight=0.
    Overall confidence capped at CONF_PARTIAL_LIVE (0.60) if any agent ignored.
    """
    agents = {
        "market_agent":    (market_conf,    market_source),
        "financial_agent": (financial_conf, financial_source),
        "knowledge_agent": (knowledge_conf, knowledge_source),
    }

    per_agent:     dict  = {}
    total_weight          = 0.0
    weighted_sum          = 0.0
    any_ignored           = False
    ignored_agents: list  = []

    for name, (conf, src) in agents.items():
        base_weight = _AGENT_WEIGHTS[name]
        ignored     = conf < IGNORE_THRESHOLD

        if ignored:
            weight      = 0.0
            any_ignored = True
            ignored_agents.append(name)
            log.warning(
                "[confidence] %s IGNORED (confidence=%.3f < threshold=%.2f)",
                name, conf, IGNORE_THRESHOLD,
            )
        else:
            weight = base_weight

        per_agent[name] = {
            "confidence":  round(conf, 4),
            "source":      src,
            "weight":      round(weight, 4),
            "base_weight": round(base_weight, 4),
            "used":        not ignored,
            "ignored":     ignored,
        }

        total_weight += weight
        weighted_sum += conf * weight

    if total_weight > 0:
        wc = weighted_sum / total_weight
    else:
        wc = MIN_VIABLE
        log.error("[confidence] ALL agents ignored — using minimum viable %.2f", MIN_VIABLE)

    # Cap if any agent ignored
    if any_ignored and wc > CONF_PARTIAL_LIVE:
        log.info("[confidence] capping %.3f → %.3f (ignored: %s)", wc, CONF_PARTIAL_LIVE, ignored_agents)
        wc = CONF_PARTIAL_LIVE

    # Learning adjustment ±0.10
    adj = max(-0.10, min(0.10, learning_adj))
    wc  = round(min(1.0, max(0.0, wc + adj)), 4)

    label = "High" if wc >= 0.80 else "Medium" if wc >= 0.60 else "Low"

    report = {
        "weighted_confidence": wc,
        "label":               label,
        "per_agent":           per_agent,
        "ignored_agents":      ignored_agents,
        "any_agent_ignored":   any_ignored,
        "total_weight_used":   round(total_weight, 4),
        "learning_adjustment": round(adj, 4),
        "is_reliable":         wc >= MIN_VIABLE and not any_ignored,
    }

    log.info(
        "[confidence] overall=%.3f label=%s ignored=%s",
        wc, label, ignored_agents,
    )
    return report
