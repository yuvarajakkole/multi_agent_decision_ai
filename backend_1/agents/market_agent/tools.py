from langchain.tools import tool
import yfinance as yf
from functools import lru_cache
from typing import Dict


# ---------------------------------------------------------
# MARKET INDEX TOOL
# ---------------------------------------------------------

@tool
@lru_cache(maxsize=64)
def fetch_market_index_data(symbol: str = "^GSPC") -> Dict:
    """
    Fetch macro market performance using an index.
    """

    ticker = yf.Ticker(symbol)

    hist = ticker.history(period="6mo")

    if hist.empty:
        return {}

    start_price = hist.iloc[0]["Close"]
    end_price = hist.iloc[-1]["Close"]

    growth = ((end_price - start_price) / start_price) * 100

    return {
        "symbol": symbol,
        "start_price": float(start_price),
        "end_price": float(end_price),
        "six_month_growth_percent": round(float(growth), 2)
    }


# ---------------------------------------------------------
# FINTECH TRENDS TOOL
# ---------------------------------------------------------

@tool
def get_fintech_trends(country: str) -> Dict:
    """
    Return major fintech trends for a country.
    """

    trends = [
        "AI-based credit scoring",
        "Open banking adoption",
        "Digital SME lending platforms",
        "Embedded finance integrations",
        "Mobile-first financial services"
    ]

    return {
        "country": country,
        "trends": trends
    }


# ---------------------------------------------------------
# COMPETITOR ANALYSIS TOOL
# ---------------------------------------------------------

@tool
def get_competitor_analysis(industry: str = "fintech lending") -> Dict:
    """
    Estimate competition landscape.
    """

    competitors = [
        "Local banks",
        "Neobanks",
        "Buy Now Pay Later providers",
        "Peer-to-peer lending platforms",
        "International fintech startups"
    ]

    return {
        "industry": industry,
        "competitor_types": competitors,
        "competition_level": "Medium"
    }


# ---------------------------------------------------------
# MARKET SIZE ESTIMATOR
# ---------------------------------------------------------

@tool
def estimate_market_size(country: str) -> Dict:
    """
    Rough fintech market estimation using heuristics.
    """

    estimates = {
        "UAE": "$2B fintech market",
        "India": "$50B fintech ecosystem",
        "Saudi Arabia": "$3B fintech market"
    }

    return {
        "country": country,
        "estimated_market_size": estimates.get(
            country,
            "Emerging fintech market"
        )
    }




# from langchain.tools import tool
# from functools import lru_cache


# @tool
# @lru_cache(maxsize=64)
# def fetch_market_news(country: str) -> str:
#     """
#     Fetch fintech market news for a country.
#     """

#     return f"Recent fintech expansion activity in {country} shows strong demand for SME lending."


# @tool
# @lru_cache(maxsize=64)
# def get_fintech_trends(country: str) -> str:
#     """
#     Return major fintech trends.
#     """

#     return "AI credit scoring, embedded finance, SME digital lending"


# @tool
# @lru_cache(maxsize=64)
# def get_market_size_estimate(country: str) -> str:
#     """
#     Estimate fintech market size.
#     """

#     return f"The fintech lending market in {country} is estimated around $2B with strong growth."


# @tool
# @lru_cache(maxsize=64)
# def get_competitor_analysis(country: str) -> str:
#     """
#     Identify competitors in fintech lending.
#     """

#     return "Local banks, neobanks, BNPL providers, international fintech platforms"