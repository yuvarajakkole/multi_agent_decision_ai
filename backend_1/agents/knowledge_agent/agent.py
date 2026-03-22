from langchain.agents import create_react_agent
from langchain.agents import AgentExecutor
from langchain_core.prompts import PromptTemplate

from config.llm_config import get_fast_llm

from .tools import (
    load_company_dataset,
    extract_company_strengths,
    analyze_past_expansions,
    evaluate_resource_capacity,
    analyze_financial_history
)

from .prompt import SYSTEM_PROMPT


tools = [
    load_company_dataset,
    extract_company_strengths,
    analyze_past_expansions,
    evaluate_resource_capacity,
    analyze_financial_history
]


def create_knowledge_agent():

    llm = get_fast_llm()

    prompt = PromptTemplate.from_template(
        SYSTEM_PROMPT +
        """
        Question: {input}

        Use tools to analyze company data.
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