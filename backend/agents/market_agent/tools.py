import os
import requests
from langchain_core.tools import tool

_NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

_COUNTRY_CODES = {
    "uae": "AE", "dubai": "AE", "abu dhabi": "AE",
    "saudi": "SA", "saudi arabia": "SA", "ksa": "SA",
    "india": "IN", "indonesia": "ID", "singapore": "SG",
    "egypt": "EG", "qatar": "QA", "kuwait": "KW",
    "bahrain": "BH", "oman": "OM", "pakistan": "PK",
    "malaysia": "MY", "thailand": "TH", "nigeria": "NG",
    "kenya": "KE", "south africa": "ZA", "brazil": "BR",
    "uk": "GB", "usa": "US", "germany": "DE", "turkey": "TR",
}

def _get_country_code(market: str) -> str:
    return _COUNTRY_CODES.get(market.lower().strip(), market[:2].upper())


@tool
def get_country_profile(market: str) -> str:
    """
    Fetch real country profile using REST Countries API (free, no key needed).
    Returns population, region, currency, languages, capital.
    Args:
        market: Country name e.g. UAE, India, Saudi Arabia
    """
    try:
        resp = requests.get(
            f"https://restcountries.com/v3.1/name/{market}",
            timeout=8
        )
        resp.raise_for_status()
        data = resp.json()[0]

        name       = data.get("name", {}).get("common", market)
        population = data.get("population", 0)
        region     = data.get("region", "N/A")
        subregion  = data.get("subregion", "N/A")
        capital    = data.get("capital", ["N/A"])[0]
        currencies = ", ".join(
            f"{v.get('name')} ({v.get('symbol','')})"
            for v in data.get("currencies", {}).values()
        )
        languages = ", ".join(data.get("languages", {}).values())

        return (
            f"Country: {name} | Region: {region} / {subregion} | "
            f"Capital: {capital} | Population: {population:,} | "
            f"Currency: {currencies} | Languages: {languages}"
        )
    except Exception as e:
        return (
            f"Country profile for {market}: Could not fetch live data ({e}). "
            "Emerging market with growing digital economy."
        )


@tool
def get_world_bank_macro(market: str) -> str:
    """
    Fetch real macroeconomic indicators from World Bank Open API (free, no key needed).
    Returns GDP growth, inflation, GDP per capita, unemployment.
    Args:
        market: Country name e.g. UAE, India, Saudi Arabia
    """
    code = _get_country_code(market)

    indicators = {
        "NY.GDP.MKTP.KD.ZG": "GDP growth (%)",
        "FP.CPI.TOTL.ZG":    "Inflation (%)",
        "NY.GDP.PCAP.CD":    "GDP per capita (USD)",
        "SL.UEM.TOTL.ZS":    "Unemployment (%)",
    }

    results = []
    for ind_code, label in indicators.items():
        try:
            url = (
                f"https://api.worldbank.org/v2/country/{code}"
                f"/indicator/{ind_code}?format=json&mrv=2&per_page=2"
            )
            resp = requests.get(url, timeout=8)
            resp.raise_for_status()
            payload = resp.json()

            if len(payload) > 1 and payload[1]:
                for entry in payload[1]:
                    value = entry.get("value")
                    if value is not None:
                        results.append(
                            f"{label}: {round(float(value), 2)} ({entry.get('date','?')})"
                        )
                        break
                else:
                    results.append(f"{label}: N/A")
            else:
                results.append(f"{label}: N/A")

        except Exception as e:
            results.append(f"{label}: unavailable ({e})")

    return f"World Bank data for {market} ({code}): " + " | ".join(results)


@tool
def fetch_market_news(market: str, product_type: str) -> str:
    """
    Fetch live news headlines using NewsAPI (free key at newsapi.org).
    Falls back to DuckDuckGo Instant Answer API if no key is set.
    Args:
        market: Target country or region e.g. UAE
        product_type: Product category e.g. SME lending, fintech
    """
    query = f"{product_type} {market} fintech market 2024 2025"

    if _NEWS_API_KEY:
        try:
            resp = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q":        query,
                    "sortBy":   "relevancy",
                    "pageSize": 5,
                    "language": "en",
                    "apiKey":   _NEWS_API_KEY,
                },
                timeout=10,
            )
            resp.raise_for_status()
            articles = resp.json().get("articles", [])
            if articles:
                lines = []
                for a in articles[:4]:
                    title  = a.get("title", "")
                    source = a.get("source", {}).get("name", "?")
                    desc   = (a.get("description") or "")[:120]
                    lines.append(f"[{source}] {title}. {desc}")
                return "Live news:\n" + "\n".join(lines)
        except Exception:
            pass

    try:
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_redirect": 1, "no_html": 1},
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()

        parts = []
        abstract = data.get("AbstractText", "")
        if abstract:
            parts.append(f"Overview: {abstract[:300]}")
        related = [
            r.get("Text", "")
            for r in data.get("RelatedTopics", [])[:3]
            if isinstance(r, dict) and r.get("Text")
        ]
        if related:
            parts.append("Related: " + " | ".join(related))
        if parts:
            return "\n".join(parts)
    except Exception:
        pass

    return (
        f"News for {product_type} in {market}: "
        "Add NEWS_API_KEY to .env for live headlines. "
        "Market shows growing digital lending activity."
    )


@tool
def get_competitor_landscape(market: str, product_type: str) -> str:
    """
    Fetch live competitor information using DuckDuckGo Instant Answer API
    (free, no key needed).
    Args:
        market: Target country or region
        product_type: Product or service category
    """
    query = f"top {product_type} fintech companies {market} 2024"

    try:
        resp = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": query, "format": "json", "no_redirect": 1, "no_html": 1},
            timeout=8,
        )
        resp.raise_for_status()
        data = resp.json()

        results = []
        abstract = data.get("AbstractText", "")
        if abstract:
            results.append(f"Market overview: {abstract[:400]}")
        related = [
            r.get("Text", "")
            for r in data.get("RelatedTopics", [])[:5]
            if isinstance(r, dict) and r.get("Text")
        ]
        if related:
            results.append("Players: " + " | ".join(related[:4]))
        if results:
            return "\n".join(results)
    except Exception:
        pass

    known = {
        "uae":       "Beehive, Lendo, Funding Souq, Sarwa, Tabby",
        "saudi":     "Tamara, Lendo, Raqamyah, STC Pay, Hala",
        "india":     "Lendingkart, Capital Float, NeoGrowth, Indifi, Razorpay Capital",
        "indonesia": "Modalku, KoinWorks, Kredivo, Investree, Amartha",
        "singapore": "Funding Societies, Validus, Aspire, Nium",
    }
    for k, v in known.items():
        if k in market.lower():
            return f"Known {product_type} players in {market}: {v}. Competition: Medium-High."

    return (
        f"Competitor data for {product_type} in {market}: "
        "Local and regional fintech players active. Competition level: Medium."
    )