def determine_agents_to_run(state):

    plan = state.get("execution_plan", [])

    agents = []

    for step in plan:

        if step == "market_agent":
            agents.append("market_agent")

        if step == "financial_agent":
            agents.append("financial_agent")

        if step == "knowledge_agent":
            agents.append("knowledge_agent")

    return agents