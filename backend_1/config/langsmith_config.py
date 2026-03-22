import os
from langsmith import Client
from .settings import (
    LANGSMITH_API_KEY,
    LANGSMITH_PROJECT,
    LANGSMITH_ENDPOINT
)

# ---------------------------------------------------------
# ENABLE LANGSMITH
# ---------------------------------------------------------

if LANGSMITH_API_KEY:

    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"] = LANGSMITH_PROJECT
    os.environ["LANGCHAIN_ENDPOINT"] = LANGSMITH_ENDPOINT

    client = Client(
        api_key=LANGSMITH_API_KEY,
        api_url=LANGSMITH_ENDPOINT
    )

else:
    client = None


def get_langsmith_client():
    """
    Returns LangSmith client if configured.
    """
    return client