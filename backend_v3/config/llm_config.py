from langchain_openai import ChatOpenAI
from config.settings import OPENAI_API_KEY,OPENAI_DEFAULT_MODEL,OPENAI_STRATEGY_MODEL
_fast=_reasoning=_comms=None
def get_fast_llm():
    global _fast
    if _fast is None: _fast=ChatOpenAI(api_key=OPENAI_API_KEY,model=OPENAI_DEFAULT_MODEL,temperature=0.1,max_tokens=3000)
    return _fast
def get_reasoning_llm():
    global _reasoning
    if _reasoning is None: _reasoning=ChatOpenAI(api_key=OPENAI_API_KEY,model=OPENAI_STRATEGY_MODEL,temperature=0.0,max_tokens=4000)
    return _reasoning
def get_communication_llm():
    global _comms
    if _comms is None: _comms=ChatOpenAI(api_key=OPENAI_API_KEY,model=OPENAI_STRATEGY_MODEL,temperature=0.1,max_tokens=4000)
    return _comms
