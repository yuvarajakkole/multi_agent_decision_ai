"""config/llm_config.py — Cached LLM instances."""

from functools import lru_cache
from langchain_openai import ChatOpenAI
from config.settings import OPENAI_API_KEY, OPENAI_FAST_MODEL, OPENAI_REASON_MODEL


@lru_cache(maxsize=1)
def get_fast_llm() -> ChatOpenAI:
    """gpt-4o-mini — market, financial, knowledge, supervisor agents."""
    return ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_FAST_MODEL,
        temperature=0.0,      # deterministic — same query = same reasoning
        max_tokens=3000,
    )


@lru_cache(maxsize=1)
def get_reason_llm() -> ChatOpenAI:
    """gpt-4o — strategy agent (weighs all evidence, produces final decision)."""
    return ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_REASON_MODEL,
        temperature=0.0,
        max_tokens=4000,
    )


@lru_cache(maxsize=1)
def get_comms_llm() -> ChatOpenAI:
    """gpt-4o — communication agent (natural language report)."""
    return ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_REASON_MODEL,
        temperature=0.1,      # slight creativity for natural language
        max_tokens=4000,
    )
