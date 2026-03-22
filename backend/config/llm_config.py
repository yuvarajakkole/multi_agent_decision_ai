from langchain_openai import ChatOpenAI
from config.settings import (
    OPENAI_API_KEY,
    OPENAI_DEFAULT_MODEL,
    OPENAI_STRATEGY_MODEL
)

# ---------------------------------------------------------
# FIX: Use module-level singletons instead of lru_cache.
# lru_cache on ChatOpenAI objects can cause issues with
# async usage. Simple None-check singletons are safer.
# ---------------------------------------------------------

_fast_llm = None
_reasoning_llm = None
_communication_llm = None


def get_fast_llm() -> ChatOpenAI:
    """
    gpt-4o-mini — used by supervisor, market, financial, knowledge agents.
    Fast and cost-efficient for analysis tasks.
    """
    global _fast_llm
    if _fast_llm is None:
        _fast_llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=OPENAI_DEFAULT_MODEL,
            temperature=0.3,
            max_tokens=2000
        )
    return _fast_llm


def get_reasoning_llm() -> ChatOpenAI:
    """
    gpt-4o — used by strategy agent.
    Deeper synthesis for decision making.
    """
    global _reasoning_llm
    if _reasoning_llm is None:
        _reasoning_llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=OPENAI_STRATEGY_MODEL,
            temperature=0.2,
            max_tokens=3000
        )
    return _reasoning_llm


def get_communication_llm() -> ChatOpenAI:
    """
    gpt-4o — used by communication agent.
    Produces clear executive-quality reports.
    """
    global _communication_llm
    if _communication_llm is None:
        _communication_llm = ChatOpenAI(
            api_key=OPENAI_API_KEY,
            model=OPENAI_STRATEGY_MODEL,
            temperature=0.1,
            max_tokens=4000
        )
    return _communication_llm
