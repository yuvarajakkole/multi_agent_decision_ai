from langchain_core.tools import tool

@tool
def build_summary(decision: str, score: float) -> str:
    """Build one-line executive summary."""
    labels = {"GO":"Expansion strongly recommended","GO_WITH_CONDITIONS":"Expansion viable with safeguards",
              "WAIT":"Opportunity requires further validation","NO_GO":"Expansion not recommended"}
    return f"{labels.get(decision, 'Decision unclear')}. Strategic score: {score:.0f}/100."

@tool
def build_risk_list(market_text: str) -> list:
    """Extract key risks from market analysis text."""
    text = market_text.lower()
    risks = []
    if "regulation" in text or "regulatory" in text: risks.append("Regulatory compliance risk")
    if "competition" in text or "competitor" in text: risks.append("Competitive market pressure")
    if "currency" in text or "fx" in text:            risks.append("Currency / FX volatility")
    if "npl" in text or "credit" in text:             risks.append("Credit / NPL risk")
    if "macro" in text or "inflation" in text:        risks.append("Macroeconomic uncertainty")
    return risks or ["General market uncertainty"]

@tool
def build_recommendations(decision: str) -> list:
    """Return action recommendations based on decision."""
    recs = {
        "GO": ["Initiate market entry strategy","Form local financial partnerships",
               "Launch pilot lending program","Set 90-day milestones"],
        "GO_WITH_CONDITIONS": ["Conduct deeper regulatory review","Partner with local institutions",
                               "Launch limited pilot","Secure risk mitigation instruments"],
        "WAIT": ["Gather additional market intelligence","Monitor regulatory developments",
                 "Build local relationships proactively","Reassess in 6 months"],
        "NO_GO": ["Reassess expansion strategy","Focus on stronger markets",
                  "Improve internal readiness","Consider adjacent markets"],
    }
    return recs.get(decision, recs["WAIT"])
