"""
core/reliability/validator.py
Every agent output passes through here before entering shared state.
Returns a standardised envelope: data, confidence, errors, warnings, source.
"""
from datetime import datetime, timezone

REQUIRED_FIELDS = {
    "market_insights": [
        "market", "gdp_growth_percent", "inflation_percent",
        "competition_level", "market_attractiveness",
    ],
    "financial_analysis": [
        "market", "estimated_roi_percent", "estimated_irr_percent",
        "payback_period_months", "risk_level", "financial_attractiveness",
    ],
    "knowledge_summary": [
        "company_name", "strategic_fit", "available_budget_usd",
        "budget_within_limits", "risk_appetite_match",
    ],
    "strategy_decision": [
        "decision", "confidence_score", "total_score", "rationale", "next_steps",
    ],
}

_DEDUCTIONS = {
    "missing_field":   0.15,
    "llm_only_source": 0.20,
    "fallback_used":   0.10,
}


def validate_agent_output(
    agent_name: str,
    output_key: str,
    raw_output: dict,
    source: str = "hybrid",
) -> dict:
    """
    Wrap agent output in reliability envelope.
    source: "tool" | "llm" | "hybrid" | "fallback"
    """
    errors = []
    warnings = []
    confidence = 1.0

    if not raw_output or not isinstance(raw_output, dict):
        errors.append("Agent returned empty or non-dict output")
        return _env(agent_name, {}, 0.20, errors, warnings, source)

    # Required field check
    for field in REQUIRED_FIELDS.get(output_key, []):
        val = raw_output.get(field)
        if val in (None, "", "N/A", "Data unavailable", "unknown"):
            errors.append(f"Missing or empty required field: '{field}'")
            confidence -= _DEDUCTIONS["missing_field"]

    # Source quality
    if source == "llm":
        warnings.append("Data sourced from LLM only — higher hallucination risk")
        confidence -= _DEDUCTIONS["llm_only_source"]
    elif source == "fallback":
        warnings.append("Primary API failed — fallback static data used")
        confidence -= _DEDUCTIONS["fallback_used"]

    # ── Financial sanity checks ────────────────────────────────────────────────
    # NOTE: IRR is a WARNING not an ERROR when negative — it means investment
    #       may not break even, but the value is valid and meaningful.
    if output_key == "financial_analysis":
        try:
            roi = float(raw_output.get("estimated_roi_percent", 0))
            irr = float(raw_output.get("estimated_irr_percent", 0))
            pb  = float(raw_output.get("payback_period_months", 0))

            # ROI: error only if truly impossible
            if not -100 <= roi <= 1000:
                errors.append(f"ROI {roi}% outside plausible range (-100 to 1000%)")
                confidence -= 0.15

            # IRR: warning if negative (unprofitable), error only if absurd
            if irr < 0:
                warnings.append(
                    f"IRR {irr}% is negative — project may not recover investment "
                    f"within the timeline. Consider extending the timeline or increasing budget efficiency."
                )
                confidence -= 0.05   # small confidence hit — data is valid, project is just risky
            elif irr > 500:
                errors.append(f"IRR {irr}% is implausibly high — check calculation inputs")
                confidence -= 0.10

            # Payback: warning only
            if pb <= 0 or pb > 600:
                warnings.append(f"Payback period {pb} months seems implausible")
                confidence -= 0.05

        except (TypeError, ValueError):
            errors.append("Financial metrics are non-numeric")
            confidence -= 0.20

    # ── Strategy decision sanity ───────────────────────────────────────────────
    if output_key == "strategy_decision":
        d = raw_output.get("decision", "")
        if d not in {"GO", "GO_WITH_CONDITIONS", "WAIT", "NO_GO"}:
            errors.append(f"Invalid decision value: '{d}'")
            confidence -= 0.30
        try:
            sc = float(raw_output.get("confidence_score", 0))
            if not 0 <= sc <= 100:
                errors.append(f"Confidence score {sc} out of 0-100")
                confidence -= 0.15
        except (TypeError, ValueError):
            errors.append("Confidence score non-numeric")
            confidence -= 0.10

    confidence = round(max(0.0, min(1.0, confidence)), 3)
    return _env(agent_name, raw_output, confidence, errors, warnings, source)


def _env(agent, data, confidence, errors, warnings, source):
    return {
        "data":         data,
        "confidence":   confidence,
        "errors":       errors,
        "warnings":     warnings,
        "source":       source,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "agent":        agent,
        "is_reliable":  confidence >= 0.50 and len(errors) == 0,
    }
