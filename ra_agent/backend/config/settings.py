"""config/settings.py"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR    = Path(__file__).resolve().parent.parent
PROJECT_DIR = BASE_DIR.parent

# Load .env from backend dir, then parent
for env_path in [BASE_DIR / ".env", PROJECT_DIR / ".env"]:
    if env_path.exists():
        load_dotenv(env_path)
        break

OPENAI_API_KEY       = os.getenv("OPENAI_API_KEY", "")
OPENAI_FAST_MODEL    = os.getenv("OPENAI_DEFAULT_MODEL",  "gpt-4o-mini")
OPENAI_REASON_MODEL  = os.getenv("OPENAI_STRATEGY_MODEL", "gpt-4o")

LANGSMITH_API_KEY    = os.getenv("LANGSMITH_API_KEY", "")
LANGSMITH_PROJECT    = os.getenv("LANGSMITH_PROJECT",  "ra-agent-system")
LANGSMITH_ENDPOINT   = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))
DEBUG    = os.getenv("DEBUG_MODE", "true").lower() == "true"

DATASET_PATH = BASE_DIR / "data" / "ra_groups_knowledge.json"
if not DATASET_PATH.exists():
    # Try parent data directory
    alt = PROJECT_DIR / "data" / "ra_groups_knowledge.json"
    if alt.exists():
        DATASET_PATH = alt
    else:
        # Last resort — look for the file anywhere in project
        for p in PROJECT_DIR.rglob("ra_groups_knowledge.json"):
            DATASET_PATH = p
            break

# Agent loop limits — prevents infinite retries
MAX_AGENT_RETRIES  = int(os.getenv("MAX_AGENT_RETRIES", "2"))
MIN_CONFIDENCE     = float(os.getenv("MIN_CONFIDENCE",  "0.55"))

# CORS
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173").split(",")

if DEBUG:
    print("─" * 52)
    print("  RA AGENT SYSTEM — CONFIG")
    print(f"  Fast model    : {OPENAI_FAST_MODEL}")
    print(f"  Reason model  : {OPENAI_REASON_MODEL}")
    print(f"  Dataset       : {DATASET_PATH}")
    print(f"  Max retries   : {MAX_AGENT_RETRIES}")
    print(f"  Min confidence: {MIN_CONFIDENCE}")
    print("─" * 52)
