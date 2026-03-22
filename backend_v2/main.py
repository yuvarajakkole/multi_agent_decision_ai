from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from config.settings import API_HOST, API_PORT
from config.langsmith_config import get_langsmith_client
from api.http_routes import router as http_router
from api.websocket_routes import router as websocket_router

app = FastAPI(
    title="RA Agent System v2",
    description="Production-Grade Multi-Agent Decision Intelligence Platform",
    version="2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

app.include_router(http_router, prefix="/api")
app.include_router(websocket_router)

# Serve index.html if present
_index = Path(__file__).resolve().parent / "index.html"
if not _index.exists():
    _index = Path(__file__).resolve().parent.parent / "index.html"

@app.get("/")
async def root():
    return {"status": "RA Agent System v2 running",
            "docs": "/docs", "health": "/api/health"}

@app.on_event("startup")
async def startup():
    print("\n✅  RA AGENT SYSTEM v2 STARTED")
    client = get_langsmith_client()
    if client:
        print("✅  LangSmith tracing enabled")

@app.on_event("shutdown")
async def shutdown():
    print("\nRA Agent System shutting down")
