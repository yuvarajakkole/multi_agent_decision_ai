"""
core/reliability/confidence.py
Weighted confidence scoring across all agents.
"""

AGENT_WEIGHTS = {
    "market_agent":    0.30,
    "financial_agent": 0.35,
    "knowledge_agent": 0.20,
    "strategy_agent":  0.15,
}
RELIABILITY_THRESHOLD = 0.50


def compute_weighted_confidence(agent_envelopes: dict) -> dict:
    """
    Args: agent_envelopes = { "market_agent": {"confidence": 0.85, ...}, ... }
    Returns dict with weighted_confidence, per_agent breakdown, unreliable_agents.
    """
    per_agent    = {}
    w_sum        = 0.0
    total_weight = 0.0
    unreliable   = []

    for name, weight in AGENT_WEIGHTS.items():
        env  = agent_envelopes.get(name, {})
        conf = env.get("confidence", 0.5)
        ok   = conf >= RELIABILITY_THRESHOLD
        per_agent[name] = {
            "confidence":   conf,
            "weight":       weight,
            "contribution": round(conf * weight, 4),
            "is_reliable":  ok,
            "errors":       env.get("errors", []),
            "source":       env.get("source", "unknown"),
        }
        w_sum        += conf * weight
        total_weight += weight
        if not ok:
            unreliable.append(name)

    wc = round(w_sum / total_weight, 3) if total_weight else 0.0
    overall = wc >= RELIABILITY_THRESHOLD and len(unreliable) <= 1

    return {
        "weighted_confidence": wc,
        "per_agent":           per_agent,
        "unreliable_agents":   unreliable,
        "overall_reliable":    overall,
        "confidence_label":    _label(wc),
    }


def adjust_decision_score(
    raw_score: float,
    market_conf: float,
    financial_conf: float,
    knowledge_conf: float,
) -> float:
    """
    Adjust strategy score by data-source confidence.
    Low-quality data shrinks the score, preventing over-confident decisions.
    """
    denom = (AGENT_WEIGHTS["market_agent"]
             + AGENT_WEIGHTS["financial_agent"]
             + AGENT_WEIGHTS["knowledge_agent"])
    avg_conf = (
        market_conf    * AGENT_WEIGHTS["market_agent"]
        + financial_conf * AGENT_WEIGHTS["financial_agent"]
        + knowledge_conf * AGENT_WEIGHTS["knowledge_agent"]
    ) / denom

    adjusted = raw_score * (0.50 + 0.50 * avg_conf)
    return round(min(100, max(0, adjusted)), 1)


def _label(c: float) -> str:
    if c >= 0.85: return "High"
    if c >= 0.65: return "Medium"
    if c >= 0.45: return "Low"
    return "Very Low"
