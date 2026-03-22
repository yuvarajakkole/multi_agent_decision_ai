from fastapi import APIRouter
from schemas.api_models import DecisionRequest, OutcomeRequest
from graph.graph_runner import run_graph
from utils.request_id import generate_request_id
from memory.outcome_tracker import record_outcome, get_history_summary

router = APIRouter()

@router.get("/health")
def health():
    return {"status": "ok", "version": "3.0"}

@router.post("/decision")
async def run_decision(req: DecisionRequest):
    rid = generate_request_id()
    state = {
        "request_id": rid,
        "user_query":  req.user_query,
        "market":      req.market,
        "company_name": req.company_name or "RA Groups",
        "budget":      req.budget or 1_000_000,
        "timeline_months": req.timeline_months or 12,
    }
    result = await run_graph(state)
    strategy   = result.get("strategy_decision", {})
    conf_report = result.get("_confidence_report", {})
    return {
        "request_id":        rid,
        "decision":          strategy,
        "confidence_report": conf_report,
        "final_confidence":  result.get("_final_confidence", 0),
        "market_insights":   result.get("market_insights", {}),
        "financial_analysis": result.get("financial_analysis", {}),
        "knowledge_summary": result.get("knowledge_summary", {}),
        "final_report":      result.get("final_report", ""),
        "decision_trace":    result.get("_decision_trace", {}),
    }

@router.post("/outcome")
async def record_real_outcome(req: OutcomeRequest):
    record_outcome(req.request_id, req.actual_outcome, req.notes or "")
    return {"status": "recorded", "request_id": req.request_id}

@router.get("/history")
def get_history():
    return get_history_summary()
