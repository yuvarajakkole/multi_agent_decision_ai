from langchain.agents.react.agent import create_react_agent
from langchain.agents import AgentExecutor
from langchain_core.prompts import PromptTemplate

from config.llm_config import get_fast_llm

from .tools import (
    calculate_roi,
    calculate_payback_period,
    fetch_financial_sector_sentiment,
    compute_risk_score
)

from .prompt import SYSTEM_PROMPT


tools = [
    calculate_roi,
    calculate_payback_period,
    fetch_financial_sector_sentiment,
    compute_risk_score
]


def create_financial_agent():

    llm = get_fast_llm()

    prompt = PromptTemplate.from_template(
        SYSTEM_PROMPT +
        """
        Question: {input}

        Think step by step.
        Use tools for calculations.
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