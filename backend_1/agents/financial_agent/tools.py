from langchain.tools import tool
import yfinance as yf
from functools import lru_cache


# ---------------------------------------------------------
# ROI CALCULATOR
# ---------------------------------------------------------

@tool
def calculate_roi(investment: float, projected_revenue: float) -> float:
    """
    Calculate Return on Investment.
    """

    if investment == 0:
        return 0

    roi = ((projected_revenue - investment) / investment) * 100

    return round(roi, 2)


# ---------------------------------------------------------
# PAYBACK PERIOD
# ---------------------------------------------------------

@tool
def calculate_payback_period(investment: float, yearly_profit: float) -> float:
    """
    Estimate payback period in months.
    """

    if yearly_profit <= 0:
        return 0

    years = investment / yearly_profit

    months = years * 12

    return round(months, 2)


# ---------------------------------------------------------
# SECTOR SENTIMENT
# ---------------------------------------------------------

@tool
@lru_cache(maxsize=64)
def fetch_financial_sector_sentiment() -> dict:
    """
    Uses XLF ETF as proxy for financial sector sentiment.
    """

    ticker = yf.Ticker("XLF")

    hist = ticker.history(period="6mo")

    if hist.empty:
        return {}

    start_price = hist.iloc[0]["Close"]
    end_price = hist.iloc[-1]["Close"]

    change = ((end_price - start_price) / start_price) * 100

    sentiment = "Neutral"

    if change > 10:
        sentiment = "Positive"

    elif change < -5:
        sentiment = "Negative"

    return {
        "sector_change_percent": round(float(change), 2),
        "sector_sentiment": sentiment
    }


# ---------------------------------------------------------
# RISK SCORING
# ---------------------------------------------------------

@tool
def compute_risk_score(
    competition_level: str,
    sector_sentiment: str
) -> float:
    """
    Compute financial risk score (0-100).
    Lower score = lower risk.
    """

    score = 50

    if competition_level == "High":
        score += 20

    if sector_sentiment == "Negative":
        score += 15

    if sector_sentiment == "Positive":
        score -= 10

    return max(min(score, 100), 0)