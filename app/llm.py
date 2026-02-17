# app/llm.py
# Shared LLM factory.

from langchain_openai import ChatOpenAI
from .config import settings

def get_llm():
    """
    Returns a ChatOpenAI model instance.
    Uses OPENAI_API_KEY from .env.
    """
    if not settings.OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set")

    return ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=0.3,
        api_key=settings.OPENAI_API_KEY,   
    )
