"""agents/communication_agent/tools.py"""

from langchain_core.tools import tool


@tool
def format_score_table(
    market_score: float,
    financial_score: float,
    strategic_score: float,
    total_score: float,
    market_driver: str,
    financial_driver: str,
    strategic_driver: str,
) -> str:
    """Format the decision score table for the report."""
    return (
        f"| Dimension     | Score      | Key Driver                     |\n"
        f"|---------------|------------|--------------------------------|\n"
        f"| Market        | {market_score:.0f}/40   | {market_driver[:32]:<32} |\n"
        f"| Financial     | {financial_score:.0f}/40   | {financial_driver[:32]:<32} |\n"
        f"| Strategic Fit | {strategic_score:.0f}/20   | {strategic_driver[:32]:<32} |\n"
        f"| **Total**     | **{total_score:.0f}/100** | Combined weighted assessment   |"
    )


@tool
def build_risk_register(risks: list, decision: str) -> str:
    """Format risks with severity markers appropriate to the decision level."""
    severity_map = {
        "GO":                 "🟡",
        "GO_WITH_CONDITIONS": "🟠",
        "WAIT":               "🔴",
        "NO_GO":              "⛔",
    }
    icon = severity_map.get(decision, "🟠")
    lines = [f"{i+1}. {icon} {r}" for i, r in enumerate(risks[:5])]
    return "\n".join(lines)
