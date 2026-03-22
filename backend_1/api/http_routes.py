# backend/api/http_routes.py

from fastapi import APIRouter

from schemas.api_models import DecisionRequest, DecisionResponse

from graph.graph_runner import run_graph

from utils.request_id import generate_request_id


router = APIRouter()


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

@router.get("/health")
def health_check():

    return {"status": "ok"}


# ---------------------------------------------------------
# DECISION ENDPOINT
# ---------------------------------------------------------

@router.post("/decision", response_model=DecisionResponse)
async def run_decision(request: DecisionRequest):

    request_id = generate_request_id()

    state = {
        "request_id": request_id,
        "user_query": request.user_query,
        "market": request.market,
        "company_name": request.company_name,
        "budget": request.budget,
        "timeline_months": request.timeline_months
    }

    result = await run_graph(state)

    return DecisionResponse(
        request_id=request_id,
        decision=result.get("strategy_decision", {}),
        market_insights=result.get("market_insights", {}),
        financial_analysis=result.get("financial_analysis", {}),
        knowledge_summary=result.get("knowledge_summary", {}),
        final_report=result.get("final_report", "")
    )