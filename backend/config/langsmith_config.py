import os
from config.settings import (
    LANGSMITH_API_KEY,
    LANGSMITH_PROJECT,
    LANGSMITH_ENDPOINT
)


def get_langsmith_client():
    """
    Configure LangSmith tracing if API key is available.
    Returns client or None if not configured.
    """

    if not LANGSMITH_API_KEY:
        print("LangSmith: No API key found. Tracing disabled.")
        return None

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
    os.environ["LANGCHAIN_ENDPOINT"] = LANGSMITH_ENDPOINT

    print(f"LangSmith: Tracing enabled → project '{LANGSMITH_PROJECT}'")
    return True
