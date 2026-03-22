from langchain.agents import create_react_agent
from langchain.agents import AgentExecutor
from langchain_core.prompts import PromptTemplate
from config.llm_config import get_fast_llm

from .supervisor_tools import (
    classify_query_type,
    build_execution_plan
)
from .supervisor_prompt import SYSTEM_PROMPT
tools = [
    classify_query_type,
    build_execution_plan
]
def create_supervisor_agent():
    llm = get_fast_llm()
    prompt = PromptTemplate.from_template(
        SYSTEM_PROMPT +
        """

You can use the following tools:

{tools}

Tool names:
{tool_names}

When solving the task follow this format:

Question: {input}
Thought: think about which tool to use
Action: the tool name from [{tool_names}]
Action Input: the input for the tool
Observation: result of the tool

Repeat Thought/Action/Action Input/Observation as needed.

Thought: I now know the final answer
Final Answer: execution plan for the agents.

{agent_scratchpad}
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
        max_iterations=3
    )