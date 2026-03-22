"""
api/http_routes.py
Production-grade HTTP routes.
Response includes: decision, confidence report, per-agent outputs,
full decision trace (explainability), and final executive report.
"""
from fastapi import APIRouter, HTTPException
from schemas.api_models import DecisionRequest, OutcomeRequest
from graph.graph_runner import run_graph
from utils.request_id import generate_request_id
from memory.outcome_tracker import record_outcome, get_history_summary

router = APIRouter()


@router.get("/health")
def health():
    return {"status": "ok", "service": "RA Agent System", "version": "2.0"}


@router.get("/history")
def history():
    """Return learning-loop summary stats for all past decisions."""
    return get_history_summary()


@router.post("/outcome")
def record_real_outcome(req: OutcomeRequest):
    """
    Record real-world outcome for a past decision.
    Drives the learning loop — future confidence scores are adjusted.
    actual_outcome: 'success' | 'failure' | 'partial'
    """
    valid = {"success", "failure", "partial"}
    if req.actual_outcome not in valid:
        raise HTTPException(400, detail=f"outcome must be one of {valid}")
    record_outcome(req.request_id, req.actual_outcome, req.notes or "")
    return {"status": "recorded", "request_id": req.request_id,
            "outcome": req.actual_outcome}


@router.post("/decision")
async def run_decision(request: DecisionRequest):
    """
    Run the full multi-agent decision pipeline.
    Returns:
      - decision (GO / GO_WITH_CONDITIONS / WAIT / NO_GO)
      - confidence_report (weighted + per-agent)
      - market_insights, financial_analysis, knowledge_summary (raw agent outputs)
      - final_report (executive markdown report)
      - decision_trace (full step-by-step explainability log)
    """
    request_id = generate_request_id()
    state = {
        "request_id":      request_id,
        "user_query":      request.user_query,
        "market":          request.market,
        "company_name":    request.company_name or "RA Groups",
        "budget":          request.budget or 1_000_000,
        "timeline_months": request.timeline_months or 12,
    }

    try:
        result = await run_graph(state)
    except Exception as e:
        raise HTTPException(500, detail=f"Pipeline failed: {e}")

    strategy    = result.get("strategy_decision", {})
    conf_report = result.get("_confidence_report", {})

    return {
        "request_id": request_id,

        # Core decision
        "decision": {
            "outcome":     strategy.get("decision", "UNKNOWN"),
            "total_score": strategy.get("total_score", 0),
            "confidence":  result.get("_final_confidence", 0),
            "rationale":   strategy.get("rationale", []),
            "key_risks":   strategy.get("key_risks", []),
            "conditions":  strategy.get("conditions", []),
            "next_steps":  strategy.get("next_steps", []),
            "summary":     strategy.get("summary", ""),
        },

        # Per-agent confidence breakdown
        "confidence_report": {
            "weighted_confidence": conf_report.get("weighted_confidence", 0),
            "confidence_label":    conf_report.get("confidence_label", "Unknown"),
            "overall_reliable":    conf_report.get("overall_reliable", False),
            "unreliable_agents":   conf_report.get("unreliable_agents", []),
            "per_agent":           conf_report.get("per_agent", {}),
        },

        # Raw agent outputs
        "market_insights":    result.get("market_insights", {}),
        "financial_analysis": result.get("financial_analysis", {}),
        "knowledge_summary":  result.get("knowledge_summary", {}),

        # Executive report
        "final_report": result.get("final_report", ""),

        # Full explainability trace
        "decision_trace": result.get("_decision_trace", {}),
    }
