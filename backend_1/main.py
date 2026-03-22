# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# configuration
from config.settings import API_HOST, API_PORT
from config.langsmith_config import get_langsmith_client

# routes
from api.http_routes import router as http_router
from api.websocket_routes import router as websocket_router


# ---------------------------------------------------------
# INITIALIZE FASTAPI
# ---------------------------------------------------------

app = FastAPI(
    title="RA Agent System",
    description="Multi-Agent Decision Intelligence Platform",
    version="1.0"
)


# ---------------------------------------------------------
# CORS
# ---------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------
# REGISTER ROUTES
# ---------------------------------------------------------

app.include_router(http_router, prefix="/api")
app.include_router(websocket_router)


# ---------------------------------------------------------
# STARTUP EVENT
# ---------------------------------------------------------

@app.on_event("startup")
async def startup_event():

    print("\n-------------------------------------")
    print("RA AGENT SYSTEM STARTED")
    print("API running")
    print("-------------------------------------\n")

    client = get_langsmith_client()

    if client:
        print("LangSmith tracing enabled")


# ---------------------------------------------------------
# SHUTDOWN EVENT
# ---------------------------------------------------------

@app.on_event("shutdown")
async def shutdown_event():

    print("\nRA Agent System shutting down\n")