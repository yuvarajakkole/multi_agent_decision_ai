from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

from config.settings import API_HOST, API_PORT
from config.langsmith_config import get_langsmith_client
from api.http_routes import router as http_router
from api.websocket_routes import router as ws_router

app = FastAPI(
    title="RA Agent System v3",
    description="Multi-Agent Decision Intelligence Platform — accurate, fair outputs",
    version="3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend if it exists
_frontend = Path(__file__).resolve().parent / "frontend_static"
if _frontend.exists():
    app.mount("/static", StaticFiles(directory=str(_frontend)), name="static")
    @app.get("/")
    def ui():
        return FileResponse(str(_frontend / "index.html"))

app.include_router(http_router, prefix="/api")
app.include_router(ws_router)

@app.on_event("startup")
async def startup():
    print("\n✅  RA AGENT SYSTEM v3 STARTED — accurate & fair multi-agent AI")
    client = get_langsmith_client()
    if client:
        print("✅  LangSmith tracing enabled")

@app.on_event("shutdown")
async def shutdown():
    print("\nRA Agent System shutting down\n")
