from fastapi import APIRouter, HTTPException
from schemas.api_models import DecisionRequest, DecisionResponse
from graph.graph_runner import run_graph
from utils.request_id import generate_request_id

router = APIRouter()


@router.get("/health")
def health_check():
    """Quick liveness check."""
    return {
        "status": "ok",
        "service": "RA Agent System",
        "version": "1.0"
    }


@router.post("/decision", response_model=DecisionResponse)
async def run_decision(request: DecisionRequest):
    """
    HTTP endpoint for running the full multi-agent decision pipeline.
    Use this for REST clients. For real-time streaming use the WebSocket endpoint.

    Example request body:
    {
        "user_query": "Should RA Groups expand its AI-based SME lending into UAE?",
        "market": "UAE",
        "budget": 2000000,
        "timeline_months": 18
    }
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
        raise HTTPException(
            status_code=500,
            detail=f"Agent pipeline failed: {str(e)}"
        )

    return DecisionResponse(
        request_id=request_id,
        decision=result.get("strategy_decision", {}),
        market_insights=result.get("market_insights", {}),
        financial_analysis=result.get("financial_analysis", {}),
        knowledge_summary=result.get("knowledge_summary", {}),
        final_report=result.get("final_report", "")
    )
