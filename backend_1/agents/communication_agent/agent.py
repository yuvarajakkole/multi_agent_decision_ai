from langchain.agents import create_react_agent
from langchain.agents import AgentExecutor
from langchain_core.prompts import PromptTemplate

from config.llm_config import get_communication_llm

from .tools import (
    build_summary,
    build_risk_list,
    build_recommendations
)

from .prompt import SYSTEM_PROMPT


tools = [
    build_summary,
    build_risk_list,
    build_recommendations
]


def create_communication_agent():

    llm = get_communication_llm()

    prompt = PromptTemplate.from_template(
        SYSTEM_PROMPT +
        """
        Question: {input}

        Produce the final decision report.
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