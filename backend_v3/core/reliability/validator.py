from datetime import datetime, timezone

REQUIRED = {
    "market_insights":   ["market","gdp_growth_percent","inflation_percent","competition_level","market_attractiveness"],
    "financial_analysis":["market","estimated_roi_percent","estimated_irr_percent","payback_period_months","risk_level","financial_attractiveness"],
    "knowledge_summary": ["company_name","strategic_fit","available_budget_usd","budget_within_limits","risk_appetite_match"],
    "strategy_decision": ["decision","confidence_score","total_score","rationale","next_steps"],
}

def validate_agent_output(agent_name, output_key, raw_output, source="hybrid") -> dict:
    errors, warnings, confidence = [], [], 1.0
    if not raw_output or not isinstance(raw_output, dict):
        return _env(agent_name, {}, 0.2, ["Empty output"], [], source)
    for f in REQUIRED.get(output_key, []):
        v = raw_output.get(f)
        if v in (None,"","N/A","Data unavailable","unknown"):
            errors.append(f"Missing: '{f}'"); confidence -= 0.12
    if source == "llm":
        warnings.append("LLM-only source"); confidence -= 0.15
    elif source == "fallback":
        warnings.append("Fallback data used"); confidence -= 0.08
    if output_key == "financial_analysis":
        try:
            roi = float(raw_output.get("estimated_roi_percent",0))
            irr = float(raw_output.get("estimated_irr_percent",0))
            if not -100<=roi<=1000: errors.append(f"ROI {roi}% implausible"); confidence-=0.15
            if irr<0: warnings.append(f"IRR {irr}% negative — project may not recover investment"); confidence-=0.05
            elif irr>500: errors.append(f"IRR {irr}% absurd"); confidence-=0.10
        except: errors.append("Financial metrics non-numeric"); confidence-=0.20
    if output_key == "strategy_decision":
        d = raw_output.get("decision","")
        if d not in {"GO","GO_WITH_CONDITIONS","WAIT","NO_GO"}:
            errors.append(f"Invalid decision: '{d}'"); confidence-=0.30
    confidence = round(max(0.0, min(1.0, confidence)), 3)
    return _env(agent_name, raw_output, confidence, errors, warnings, source)

def _env(agent, data, confidence, errors, warnings, source):
    return {"data":data,"confidence":confidence,"errors":errors,"warnings":warnings,
            "source":source,"validated_at":datetime.now(timezone.utc).isoformat(),
            "agent":agent,"is_reliable":confidence>=0.50 and len(errors)==0}
