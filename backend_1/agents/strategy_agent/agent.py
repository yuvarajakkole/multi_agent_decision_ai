from langchain.agents import create_react_agent
from langchain.agents import AgentExecutor
from langchain_core.prompts import PromptTemplate

from config.llm_config import get_reasoning_llm

from .tools import (
    compute_market_score,
    compute_financial_score,
    compute_strategic_fit_score,
    compute_final_decision
)

from .prompt import SYSTEM_PROMPT


tools = [
    compute_market_score,
    compute_financial_score,
    compute_strategic_fit_score,
    compute_final_decision
]


def create_strategy_agent():

    llm = get_reasoning_llm()

    prompt = PromptTemplate.from_template(
        SYSTEM_PROMPT +
        """
        Question: {input}

        Use tools to compute scores
        and determine the final strategy decision.
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