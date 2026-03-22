from langchain.tools import tool


# ---------------------------------------------------------
# FORMAT EXECUTIVE SUMMARY
# ---------------------------------------------------------

@tool
def build_summary(decision: str, score: float) -> str:
    """Build executive summary based on decision and score."""

    if decision == "GO":
        return f"Expansion is recommended. Strategic score {score}."

    if decision == "GO_WITH_CONDITIONS":
        return f"Expansion appears promising but requires safeguards. Score {score}."

    if decision == "WAIT":
        return f"Opportunity requires further validation. Score {score}."

    return f"Expansion not recommended due to weak fundamentals. Score {score}."


# ---------------------------------------------------------
# BUILD RISK LIST
# ---------------------------------------------------------

@tool
def build_risk_list(market_text: str):
    """Build list of key risks based on market analysis text."""

    risks = []

    text = market_text.lower()

    if "regulation" in text:
        risks.append("Regulatory approval risks")

    if "competition" in text:
        risks.append("Competitive pressure")

    if "market volatility" in text:
        risks.append("Macroeconomic uncertainty")

    if not risks:
        risks.append("General market uncertainty")

    return risks


# ---------------------------------------------------------
# BUILD RECOMMENDATIONS
# ---------------------------------------------------------

@tool
def build_recommendations(decision: str):
    """Build list of strategic recommendations based on final decision."""

    if decision == "GO":

        return [
            "Initiate market entry strategy",
            "Form local financial partnerships",
            "Launch pilot lending program"
        ]

    if decision == "GO_WITH_CONDITIONS":

        return [
            "Conduct deeper regulatory review",
            "Partner with local banking institutions",
            "Launch limited pilot deployment"
        ]

    if decision == "WAIT":

        return [
            "Gather additional market intelligence",
            "Evaluate competitive landscape",
            "Monitor regulatory developments"
        ]

    return [
        "Reassess expansion strategy",
        "Focus on stronger markets",
        "Improve internal readiness"
    ]