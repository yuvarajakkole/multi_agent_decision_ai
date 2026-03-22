import os
from pathlib import Path
from dotenv import load_dotenv

# ---------------------------------------------------------
# BASE PATHS
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BASE_DIR.parent

ENV_PATH = BASE_DIR / ".env"

# ---------------------------------------------------------
# LOAD ENV VARIABLES
# ---------------------------------------------------------

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    raise FileNotFoundError(f".env file not found at {ENV_PATH}")

# ---------------------------------------------------------
# OPENAI SETTINGS
# ---------------------------------------------------------

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY not found in environment variables."
    )

OPENAI_DEFAULT_MODEL = os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o-mini")
OPENAI_STRATEGY_MODEL = os.getenv("OPENAI_STRATEGY_MODEL", "gpt-4o")

# ---------------------------------------------------------
# LANGSMITH SETTINGS
# ---------------------------------------------------------

LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "ra-agent-system")
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

# ---------------------------------------------------------
# SERVER SETTINGS
# ---------------------------------------------------------

API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# ---------------------------------------------------------
# MEMORY SETTINGS
# ---------------------------------------------------------

MAX_AGENT_ITERATIONS = int(os.getenv("MAX_AGENT_ITERATIONS", "4"))

# ---------------------------------------------------------
# DATASET PATH
# ---------------------------------------------------------

DATASET_PATH = PROJECT_ROOT / "data" / "ra_groups_knowledge.json"

if not DATASET_PATH.exists():
    raise FileNotFoundError(
        f"Company dataset not found at {DATASET_PATH}"
    )

# ---------------------------------------------------------
# TOOL CACHE SETTINGS
# ---------------------------------------------------------

TOOL_CACHE_SIZE = int(os.getenv("TOOL_CACHE_SIZE", "128"))

# ---------------------------------------------------------
# DEBUG
# ---------------------------------------------------------

DEBUG_MODE = os.getenv("DEBUG_MODE", "true").lower() == "true"

# ---------------------------------------------------------
# PRINT CONFIG (optional debug)
# ---------------------------------------------------------

if DEBUG_MODE:
    print("--------------------------------------------------")
    print("RA AGENT SYSTEM CONFIG LOADED")
    print("OPENAI MODEL (default):", OPENAI_DEFAULT_MODEL)
    print("OPENAI MODEL (strategy):", OPENAI_STRATEGY_MODEL)
    print("DATASET PATH:", DATASET_PATH)
    print("API HOST:", API_HOST)
    print("API PORT:", API_PORT)
    print("--------------------------------------------------")