from langchain.agents import create_react_agent
from langchain.agents import AgentExecutor
from langchain_core.prompts import PromptTemplate

from config.llm_config import get_fast_llm

from .tools import (
    fetch_market_index_data,
    get_fintech_trends,
    get_competitor_analysis,
    estimate_market_size
)

from .prompt import SYSTEM_PROMPT


tools = [
    fetch_market_index_data,
    get_fintech_trends,
    get_competitor_analysis,
    estimate_market_size
]


def create_market_agent():

    llm = get_fast_llm()

    prompt = PromptTemplate.from_template(
        SYSTEM_PROMPT +
        """
        Question: {input}

        Think step by step.
        Use tools if needed.
        """
    )

    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=False,
        max_iterations=4
    )