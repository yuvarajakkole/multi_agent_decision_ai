"""
agents/market_agent/tools.py

Live data tools. Each tool hits a real API and falls back only if it fails.
Source and confidence always surfaced — no silent fallback.
"""

import requests
from langchain_core.tools import tool
from core.reliability.market_data import resolve_iso, get_macro, get_market_profile

_HTTP_TIMEOUT = 8


def _safe_iso(market: str) -> str:
    iso = resolve_iso(market)
    return iso if iso is not None else "UNKNOWN"


@tool
def get_country_profile(market: str) -> dict:
    """
    Fetch country profile: population, currency, region.
    Source: REST Countries API (live). Returns source and confidence.
    """
    code = _safe_iso(market)
    if code == "UNKNOWN":
        return {
            "source": "unknown", "confidence": 0.0, "ignore": True,
            "country": market,
            "error": f"'{market}' could not be resolved to a known country",
        }
    try:
        r = requests.get(f"https://restcountries.com/v3.1/alpha/{code}", timeout=_HTTP_TIMEOUT)
        r.raise_for_status()
        d = r.json()[0]
        currencies = list(d.get("currencies", {}).keys())
        return {
            "source": "REST Countries API (live)", "confidence": 1.0, "ignore": False,
            "country":   d.get("name", {}).get("common", market),
            "code":      code,
            "region":    d.get("region", ""),
            "subregion": d.get("subregion", ""),
            "population": d.get("population", 0),
            "currency":  currencies[0] if currencies else "N/A",
            "languages": list(d.get("languages", {}).values())[:3],
        }
    except Exception as e:
        return {
            "source": "api_error", "confidence": 0.2, "ignore": False,
            "country": market, "code": code,
            "error": f"REST Countries failed: {type(e).__name__}: {e}",
        }


@tool
def get_world_bank_data(market: str) -> dict:
    """
    Fetch real macro indicators from World Bank API (free, no key needed).
    Returns: GDP growth, inflation, lending rate, GDP per capita, unemployment.
    Always reports which indicators came from live API vs static fallback.
    """
    env  = get_macro(market)
    data = env["data"]

    out = {
        "source":     env["source"],
        "confidence": env["confidence"],
        "ignore":     env["ignore"],
        "warnings":   env["warnings"],
        "country_code":      data.get("country_code", "UNKNOWN"),
        "gdp_growth_pct":    data.get("gdp_growth"),
        "inflation_pct":     data.get("inflation"),
        "lending_rate_pct":  data.get("lending_rate"),
        "gdp_per_capita_usd": data.get("gdp_per_capita_usd"),
        "unemployment_pct":  data.get("unemployment_pct"),
        "fintech_maturity":  data.get("fintech_maturity"),
        "macro_risk":        data.get("macro_risk"),
        "country_name":      data.get("country_name"),
        "population":        data.get("population"),
        "currency":          data.get("currency_code"),
        "exchange_rate_usd": data.get("exchange_rate_usd"),
    }

    # Add data quality field for LLM to use in its assessment
    live_count = sum(1 for k in ["gdp_growth_pct", "inflation_pct", "lending_rate_pct"]
                     if out.get(k) is not None)
    out["live_indicators_count"] = live_count
    out["data_quality"] = (
        "High"   if live_count >= 3 and env["source"] == "live_api"   else
        "Medium" if live_count >= 1 and "live" in env["source"]       else
        "Low"
    )

    if env["ignore"]:
        out["NOTE"] = f"Confidence={env['confidence']:.2f} — market data below threshold"

    return out


@tool
def get_market_size(market: str, product_type: str) -> dict:
    """
    Returns market size, growth rate, competition, regulatory environment.
    Source is static benchmarks — confidence=0.30, clearly labelled.
    """
    from core.calculations.financial import classify_product
    p_class = classify_product(product_type)
    env     = get_market_profile(market, p_class)
    data    = env["data"]

    _competitors = {
        "lending":       ["Local commercial banks","Digital NBFCs","Microfinance institutions","BNPL providers"],
        "ai_services":   ["Global AI platforms","Local AI startups","SaaS incumbents","Niche AI tools"],
        "manufacturing": ["Established OEMs","Contract manufacturers","International players"],
        "edtech":        ["Global edtech platforms","Local schools","Tutoring startups"],
        "payments":      ["Banks","Mobile money operators","International gateways"],
        "saas":          ["Global SaaS platforms","Local software companies","Open source"],
    }

    return {
        "source":            env["source"],
        "confidence":        env["confidence"],
        "ignore":            env["ignore"],
        "warnings":          env["warnings"],
        "country_code":      data.get("country_code", "UNKNOWN"),
        "product_class":     p_class,
        "market_size":       data.get("market_size"),
        "annual_growth_pct": data.get("annual_growth_pct"),
        "competition":       data.get("competition"),
        "regulatory":        data.get("regulatory"),
        "competitor_types":  _competitors.get(p_class, _competitors["lending"]),
        "data_note":         "Static estimates — treat as indicative",
    }


@tool
def search_market_news(market: str, product_type: str) -> dict:
    """
    Query DuckDuckGo Instant Answer API for recent market signals.
    Returns real snippets or explicitly notes unavailability.
    """
    queries = [
        f"{product_type} {market} market 2024 2025 growth investment",
        f"fintech {market} {product_type} opportunity 2024",
    ]
    results = []
    for q in queries:
        try:
            r = requests.get(
                "https://api.duckduckgo.com/",
                params={"q": q, "format": "json", "no_redirect": 1},
                timeout=6,
            )
            d    = r.json()
            text = d.get("AbstractText", "") or d.get("Answer", "")
            if text and len(text) > 20:
                results.append({"query": q, "snippet": text[:300]})
        except Exception:
            pass

    live = len(results) > 0
    return {
        "source":    "DuckDuckGo Instant Answer" if live else "search_unavailable",
        "confidence": 0.6 if live else 0.1,
        "ignore":    not live,
        "market":    market,
        "product":   product_type,
        "results":   results,
        "warning":   None if live else "Live search unavailable — no real-time signals retrieved.",
    }
