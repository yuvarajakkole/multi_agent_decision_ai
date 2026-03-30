"""
agents/market_agent/tools.py

All tools for the market agent.
Each tool calls a real external API with fallback to static benchmarks.
"""

import requests
from typing import Optional
from langchain_core.tools import tool
from core.reliability.market_data import iso_code, get_macro, get_market_profile

_WB_BASE = "https://api.worldbank.org/v2/country/{code}/indicator/{ind}?format=json&mrv=3&per_page=3"


@tool
def get_country_profile(market: str) -> dict:
    """
    Fetch country profile: population, currency, region, sub-region.
    Uses REST Countries API with static fallback.
    """
    code = iso_code(market)
    try:
        r = requests.get(
            f"https://restcountries.com/v3.1/alpha/{code}",
            timeout=8
        )
        r.raise_for_status()
        d = r.json()[0]
        currencies = list(d.get("currencies", {}).keys())
        return {
            "source":      "REST Countries API",
            "country":     d.get("name", {}).get("common", market),
            "code":        code,
            "region":      d.get("region", ""),
            "subregion":   d.get("subregion", ""),
            "population":  d.get("population", 0),
            "currency":    currencies[0] if currencies else "N/A",
            "languages":   list(d.get("languages", {}).values())[:3],
        }
    except Exception as e:
        fb = get_macro(market)
        return {
            "source":    "static_fallback",
            "country":   market,
            "code":      code,
            "region":    "Unknown",
            "population": 0,
            "currency":  "N/A",
            "_error":    str(e),
        }


@tool
def get_world_bank_data(market: str) -> dict:
    """
    Fetch real macroeconomic indicators from World Bank (free, no API key).
    Returns GDP growth, inflation, lending rate, GDP per capita.
    """
    code = iso_code(market)
    indicators = {
        "NY.GDP.MKTP.KD.ZG": "gdp_growth_pct",
        "FP.CPI.TOTL.ZG":    "inflation_pct",
        "FR.INR.LEND":       "lending_rate_pct",
        "NY.GDP.PCAP.CD":    "gdp_per_capita_usd",
        "SL.UEM.TOTL.ZS":   "unemployment_pct",
    }
    out = {"source": "World Bank API", "country_code": code}
    any_live = False
    for ind, key in indicators.items():
        try:
            r = requests.get(_WB_BASE.format(code=code, ind=ind), timeout=10)
            data = r.json()
            val = next(
                (e["value"] for e in (data[1] or []) if e.get("value") is not None),
                None
            )
            out[key] = round(float(val), 2) if val is not None else None
            if val is not None:
                any_live = True
        except Exception:
            out[key] = None

    # Fill missing lending rate from static fallback
    if out.get("lending_rate_pct") is None:
        fb = get_macro(market)
        out["lending_rate_pct"]   = fb["lending_rate"]
        out["_lending_rate_src"] = "static_fallback"

    out["data_quality"] = "High" if any_live else "Low (all fallback)"
    return out


@tool
def get_market_size(market: str, product_type: str) -> dict:
    """
    Returns market size, growth rate, competition level, and regulatory environment
    for this specific product type and market.
    Sourced from curated industry benchmarks validated against public reports.
    """
    from core.calculations.financial import classify_product
    code    = iso_code(market)
    p_class = classify_product(product_type)
    profile = get_market_profile(market, p_class)

    # Product-specific competitor types
    _competitors = {
        "lending":     ["Local commercial banks", "Digital NBFCs/fintechs",
                        "International lending platforms", "Microfinance institutions",
                        "BNPL providers"],
        "non_lending": ["Global SaaS/tech platforms", "Local software startups",
                        "Traditional service providers", "Niche vertical specialists",
                        "Mobile-first apps"],
    }

    # Fintech maturity from static macro data
    fb = get_macro(market)

    return {
        "source":            profile["source"],
        "country_code":      code,
        "product_class":     p_class,
        "market_size":       profile["market_size"],
        "annual_growth_pct": profile["annual_growth_pct"],
        "competition":       profile["competition"],
        "regulatory":        profile["regulatory"],
        "fintech_maturity":  fb.get("fintech_maturity", "Unknown"),
        "macro_risk":        fb.get("macro_risk", "Medium"),
        "competitor_types":  _competitors[p_class],
        "note": "Estimates from industry benchmarks — verify before investment decision",
    }


@tool
def search_market_news(market: str, product_type: str) -> dict:
    """
    Search DuckDuckGo for recent signals about this product in this market.
    Returns snippets from top results.
    """
    queries = [
        f"{product_type} {market} market 2024 2025 growth opportunity",
        f"fintech {product_type} {market} competition regulation 2024",
        f"{market} {product_type} startup investment ecosystem",
    ]
    results = []
    for q in queries:
        try:
            r = requests.get(
                "https://api.duckduckgo.com/",
                params={"q": q, "format": "json", "no_redirect": 1},
                timeout=8,
            )
            d = r.json()
            text = d.get("AbstractText", "") or d.get("Answer", "")
            if text:
                results.append({"query": q, "snippet": text[:300]})
        except Exception:
            pass

    if not results:
        results.append({
            "query": queries[0],
            "snippet": f"Live search unavailable. {market} {product_type} market context not retrieved.",
        })

    return {
        "source":      "DuckDuckGo",
        "market":      market,
        "product":     product_type,
        "results":     results,
        "live_data":   len(results) > 0 and "unavailable" not in results[0].get("snippet", ""),
    }
