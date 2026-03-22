import os; from pathlib import Path; from dotenv import load_dotenv
BASE_DIR=Path(__file__).resolve().parent.parent
PROJECT_ROOT=BASE_DIR.parent
ENV_PATH=BASE_DIR/".env"
if ENV_PATH.exists(): load_dotenv(ENV_PATH)
else: load_dotenv()
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY","")
OPENAI_DEFAULT_MODEL=os.getenv("OPENAI_DEFAULT_MODEL","gpt-4o-mini")
OPENAI_STRATEGY_MODEL=os.getenv("OPENAI_STRATEGY_MODEL","gpt-4o")
LANGSMITH_API_KEY=os.getenv("LANGSMITH_API_KEY","")
LANGSMITH_PROJECT=os.getenv("LANGSMITH_PROJECT","ra-agent-system")
LANGSMITH_ENDPOINT=os.getenv("LANGSMITH_ENDPOINT","https://api.smith.langchain.com")
API_HOST=os.getenv("API_HOST","0.0.0.0"); API_PORT=int(os.getenv("API_PORT","8000"))
DEBUG_MODE=os.getenv("DEBUG_MODE","true").lower()=="true"
DATASET_PATH=BASE_DIR/"data"/"ra_groups_knowledge.json"
if not DATASET_PATH.exists(): DATASET_PATH=PROJECT_ROOT/"data"/"ra_groups_knowledge.json"
if DEBUG_MODE:
    print("--------------------------------------------------")
    print(f"RA AGENT SYSTEM CONFIG LOADED")
    print(f"OPENAI MODEL (default)  : {OPENAI_DEFAULT_MODEL}")
    print(f"OPENAI MODEL (strategy) : {OPENAI_STRATEGY_MODEL}")
    print(f"DATASET PATH            : {DATASET_PATH}")
    print(f"API HOST                : {API_HOST}")
    print(f"API PORT                : {API_PORT}")
    print("--------------------------------------------------")
