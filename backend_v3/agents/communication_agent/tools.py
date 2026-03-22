from langchain_core.tools import tool

@tool
def format_decision_headline(decision: str, score: float, market: str, product: str) -> str:
    "Format the decision headline for the executive report."
    icons={"GO":"✅","GO_WITH_CONDITIONS":"⚠️","WAIT":"⏳","NO_GO":"❌"}
    labels={"GO":"PROCEED","GO_WITH_CONDITIONS":"PROCEED WITH CONDITIONS","WAIT":"HOLD — REASSESS IN 6 MONTHS","NO_GO":"DO NOT PROCEED"}
    return f"{icons.get(decision,'?')} {labels.get(decision,decision)} — {product} in {market} (Score: {score:.0f}/100)"

@tool
def build_risk_register(risk_factors: list, decision: str) -> list:
    "Build a structured risk register from agent data."
    severity={"GO":"Low","GO_WITH_CONDITIONS":"Medium","WAIT":"High","NO_GO":"Critical"}
    return [{"risk":r,"severity":severity.get(decision,"Medium"),"mitigation":f"Monitor and address '{r}' before deployment"} for r in risk_factors[:5]]
