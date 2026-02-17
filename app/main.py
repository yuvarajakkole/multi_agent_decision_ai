# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from .models import DecisionRequest, DecisionResponse
from .graph import run_decision_graph
app = FastAPI(
    title="RA Groups Multi-Agent Decision System",
    description="LangGraph-based multi-agent decision support for RA Groups.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Serve /static/* and root /
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
@app.get("/")
def serve_frontend():
  return FileResponse(STATIC_DIR / "index.html")
@app.get("/health")
def health():
    return {"status": "ok"}
@app.post("/decide", response_model=DecisionResponse)
def decide(request: DecisionRequest):
    initial_state = {
        "business_query": request.business_query,
        "market": request.market,
        "company_name": request.company_name,
        "budget": request.budget,
        "timeline_months": request.timeline_months,
    }
    final_state = run_decision_graph(initial_state)
    return DecisionResponse(
        final_report_markdown=final_state.get("final_report_markdown", ""),
        strategy_recommendation=final_state.get("strategy_recommendation", {}),
        market_insights=final_state.get("market_insights", {}),
        financial_analysis=final_state.get("financial_analysis", {}),
        knowledge_summary=final_state.get("knowledge_summary", {}),
    )
