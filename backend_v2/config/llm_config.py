from langchain_openai import ChatOpenAI
from config.settings import OPENAI_API_KEY, OPENAI_DEFAULT_MODEL, OPENAI_STRATEGY_MODEL

# Module-level singletons — created once, reused across agents
_fast_llm          = None
_reasoning_llm     = None
_communication_llm = None


def get_fast_llm() -> ChatOpenAI:
    global _fast_llm
    if _fast_llm is None:
        _fast_llm = ChatOpenAI(
            api_key=OPENAI_API_KEY, model=OPENAI_DEFAULT_MODEL,
            temperature=0.2, max_tokens=2500,
        )
    return _fast_llm


def get_reasoning_llm() -> ChatOpenAI:
    global _reasoning_llm
    if _reasoning_llm is None:
        _reasoning_llm = ChatOpenAI(
            api_key=OPENAI_API_KEY, model=OPENAI_STRATEGY_MODEL,
            temperature=0.1, max_tokens=4000,
        )
    return _reasoning_llm


def get_communication_llm() -> ChatOpenAI:
    global _communication_llm
    if _communication_llm is None:
        _communication_llm = ChatOpenAI(
            api_key=OPENAI_API_KEY, model=OPENAI_STRATEGY_MODEL,
            temperature=0.1, max_tokens=4000,
        )
    return _communication_llm
