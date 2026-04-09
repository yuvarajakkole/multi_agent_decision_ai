"""
config/llm_config.py

FIX: temperature=0 on ALL models — removes LLM randomness entirely.
Same input → same output. No more score=54.1 vs score=47.1 on same query.
"""

from functools import lru_cache
from langchain_openai import ChatOpenAI
from config.settings import OPENAI_API_KEY, OPENAI_FAST_MODEL, OPENAI_REASON_MODEL


@lru_cache(maxsize=1)
def get_fast_llm() -> ChatOpenAI:
    """Market, financial, knowledge, supervisor agents — deterministic."""
    return ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_FAST_MODEL,
        temperature=0,        # ← FIXED: was 0.1
        max_tokens=3000,
        seed=42,              # reproducible across identical calls
    )


@lru_cache(maxsize=1)
def get_reason_llm() -> ChatOpenAI:
    """Strategy agent — must be fully deterministic."""
    return ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_REASON_MODEL,
        temperature=0,        # ← FIXED: was 0.0 (same, kept explicit)
        max_tokens=4000,
        seed=42,
    )


@lru_cache(maxsize=1)
def get_comms_llm() -> ChatOpenAI:
    """Communication agent — slight variation acceptable for natural language."""
    return ChatOpenAI(
        api_key=OPENAI_API_KEY,
        model=OPENAI_REASON_MODEL,
        temperature=0,        # ← FIXED: was 0.1, now 0 for consistency
        max_tokens=4000,
        seed=42,
    )
