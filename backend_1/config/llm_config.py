from functools import lru_cache
from langchain_openai import ChatOpenAI
from .settings import (
    OPENAI_API_KEY,
    OPENAI_DEFAULT_MODEL,
    OPENAI_STRATEGY_MODEL
)

# ---------------------------------------------------------
# FAST MODEL (MOST AGENTS)
# ---------------------------------------------------------

@lru_cache(maxsize=2)
def get_fast_llm():
    """
    Used by:
    - supervisor
    - market agent
    - financial agent
    - knowledge agent
    """

    return ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_DEFAULT_MODEL,
        temperature=0.3,
        max_tokens=2000
    )


# ---------------------------------------------------------
# REASONING MODEL (STRATEGY)
# ---------------------------------------------------------

@lru_cache(maxsize=2)
def get_reasoning_llm():
    """
    Used by:
    - strategy agent
    """

    return ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_STRATEGY_MODEL,
        temperature=0.2,
        max_tokens=3000
    )


# ---------------------------------------------------------
# COMMUNICATION MODEL
# ---------------------------------------------------------

@lru_cache(maxsize=2)
def get_communication_llm():
    """
    Used by:
    - communication agent
    """

    return ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_STRATEGY_MODEL,
        temperature=0.1,
        max_tokens=4000
    )