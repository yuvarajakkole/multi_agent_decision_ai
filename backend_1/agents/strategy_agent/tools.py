from langchain.tools import tool


# ---------------------------------------------------------
# MARKET SCORE
# ---------------------------------------------------------

@tool
def compute_market_score(market_insights: dict) -> float:
    """Compute market score based on key insights from market analysis."""

    score = 50

    text = str(market_insights).lower()

    if "high" in text:
        score += 20

    if "medium" in text:
        score += 10

    if "low" in text:
        score -= 15

    return max(min(score, 100), 0)


# ---------------------------------------------------------
# FINANCIAL SCORE
# ---------------------------------------------------------

@tool
def compute_financial_score(financial_analysis: dict) -> float:
    """Compute financial score based on key insights from financial analysis."""

    score = 50

    text = str(financial_analysis).lower()

    if "strong" in text:
        score += 20

    if "moderate" in text:
        score += 10

    if "weak" in text:
        score -= 20

    return max(min(score, 100), 0)


# ---------------------------------------------------------
# STRATEGIC FIT SCORE
# ---------------------------------------------------------

@tool
def compute_strategic_fit_score(knowledge_summary: dict) -> float:
    """Compute strategic fit score based on key insights from company knowledge analysis."""

    score = 50

    text = str(knowledge_summary).lower()

    if "strong" in text:
        score += 20

    if "resource" in text:
        score += 10

    if "weak" in text:
        score -= 15

    return max(min(score, 100), 0)


# ---------------------------------------------------------
# FINAL DECISION ENGINE
# ---------------------------------------------------------

@tool
def compute_final_decision(
    market_score: float,
    financial_score: float,
    strategic_score: float
) -> dict:
    """Compute final decision based on weighted scores from market, financial, and strategic analyses."""

    final_score = (
        market_score * 0.35 +
        financial_score * 0.40 +
        strategic_score * 0.25
    )

    if final_score >= 75:
        decision = "GO"

    elif final_score >= 60:
        decision = "GO_WITH_CONDITIONS"

    elif final_score >= 45:
        decision = "WAIT"

    else:
        decision = "NO_GO"

    confidence = min(95, final_score)

    return {
        "decision": decision,
        "confidence": round(confidence, 2),
        "final_score": round(final_score, 2)
    }