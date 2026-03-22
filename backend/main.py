from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import API_HOST, API_PORT
from config.langsmith_config import get_langsmith_client
from api.http_routes import router as http_router
from api.websocket_routes import router as websocket_router


# ---------------------------------------------------------
# LIFESPAN — replaces deprecated @app.on_event("startup")
# ---------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("\n" + "=" * 50)
    print("  RA AGENT SYSTEM — Starting Up")
    print("=" * 50)

    get_langsmith_client()

    print(f"  HTTP  → http://{API_HOST}:{API_PORT}/api/health")
    print(f"  Docs  → http://{API_HOST}:{API_PORT}/docs")
    print(f"  WS    → ws://{API_HOST}:{API_PORT}/ws/decision")
    print("=" * 50 + "\n")

    yield  # app is running

    # Shutdown
    print("\nRA Agent System shutting down.\n")


# ---------------------------------------------------------
# APP INIT
# ---------------------------------------------------------

app = FastAPI(
    title="RA Agent System",
    description="Multi-Agent Business Decision Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------
# CORS — allow frontend dev server
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------

app.include_router(http_router,       prefix="/api")
app.include_router(websocket_router)


# ---------------------------------------------------------
# ROOT
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "status":  "RA Agent System running",
        "service": "multi-agent decision engine",
        "docs":    "/docs",
        "health":  "/api/health",
        "ws":      "/ws/decision",
    }
