def determine_agents_to_run(state):
    return state.get("agents_to_run",["market_agent","financial_agent","knowledge_agent","strategy_agent","communication_agent"])
