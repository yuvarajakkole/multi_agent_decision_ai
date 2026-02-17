# app/nodes/knowledge_agent.py
# Knowledge Agent using only local synthetic dataset for RA Groups.

from typing import Dict
from langchain_core.runnables import RunnableConfig
from ..llm import get_llm
from ..models import DecisionState
from ..data_loader import load_ra_groups_knowledge


def knowledge_agent_node(state: DecisionState, config: RunnableConfig) -> DecisionState:
    """
    Knowledge Agent:
    - Loads RA Groups' synthetic internal data from JSON file.
    - Asks LLM to summarize it into decision-relevant context.
    """
    llm = get_llm()

    business_query = state.get("business_query", "")
    company_name = state.get("company_name", "RA Groups")

    # Load local synthetic dataset
    knowledge = load_ra_groups_knowledge() or {}

    prompt = f"""
You are the Knowledge Agent for RA Groups.

Business question: {business_query}
Company name: {company_name}

Here is the internal synthetic dataset for RA Groups:
{knowledge}

Using ONLY this dataset, plus reasonable assumptions if needed:

Return a JSON-like dictionary with keys:

- company_strengths (list of strings)
- company_weaknesses (list of strings)
- relevant_past_expansions (list of objects: market, year, outcome, key_lessons)
- financial_health_summary (2-4 sentences about revenue and margins)
- risk_policy_summary (2-4 sentences)
- resource_availability_summary (2-4 sentences)
- strategic_fit_comment (3-5 sentences describing how well this new move fits RA Groups' strategy)

Keep it concise but specific. Output plain text that looks like JSON.
    """

    answer = llm.invoke(prompt)

    result: Dict = {
        "raw_text": answer.content,
        "raw_dataset_snapshot": knowledge,
    }

    return {"knowledge_summary": result}
