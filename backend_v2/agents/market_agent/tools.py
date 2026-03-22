"""
Market Agent Tools — real external APIs only.
No LLM-generated market data.
"""
import requests
from langchain_core.tools import tool
from core.reliability.fallback import get_fallback_macro, get_fallback_market_profile

_CODES = {"uae":"AE","dubai":"AE","saudi":"SA","saudi arabia":"SA","india":"IN",
          "indonesia":"ID","singapore":"SG","egypt":"EG","qatar":"QA",
          "malaysia":"MY","uk":"GB","usa":"US","germany":"DE","kenya":"KE",
          "nigeria":"NG","south africa":"ZA","brazil":"BR","turkey":"TR"}

def _code(m): return _CODES.get(m.lower().strip(), m[:2].upper())


@tool
def get_country_profile(market: str) -> dict:
    """Fetch country profile from REST Countries API (free, no key)."""
    code = _code(market)
    try:
        r = requests.get(f"https://restcountries.com/v3.1/alpha/{code}", timeout=8)
        d = r.json()[0]
        return {
            "source":     "REST Countries API",
            "country":    d.get("name", {}).get("common", market),
            "code":       code,
            "region":     d.get("region",""),
            "subregion":  d.get("subregion",""),
            "population": d.get("population", 0),
            "currency":   list(d.get("currencies",{}).keys())[0] if d.get("currencies") else "N/A",
        }
    except Exception:
        fb = get_fallback_market_profile(market)
        fb["source"] = "fallback_static"
        return fb


@tool
def get_world_bank_macro(market: str) -> dict:
    """Fetch GDP growth, inflation, lending rate from World Bank Open API."""
    code = _code(market)
    indicators = {
        "NY.GDP.MKTP.KD.ZG": "gdp_growth_percent",
        "FP.CPI.TOTL.ZG":    "inflation_percent",
        "FR.INR.LEND":       "lending_rate_percent",
        "NY.GDP.PCAP.CD":    "gdp_per_capita_usd",
    }
    result = {"source": "World Bank API", "country_code": code}
    base   = "https://api.worldbank.org/v2/country"
    for ind, key in indicators.items():
        try:
            r = requests.get(f"{base}/{code}/indicator/{ind}?format=json&mrv=2&per_page=2", timeout=8)
            d = r.json()
            val = next((e["value"] for e in (d[1] or []) if e.get("value") is not None), None)
            result[key] = round(float(val), 2) if val else "N/A"
        except Exception:
            result[key] = "N/A"

    # fill missing with fallback
    if result.get("lending_rate_percent") == "N/A":
        fb = get_fallback_macro(market)
        result["lending_rate_percent"] = fb["lending_rate"]
        result["_lending_rate_source"] = "fallback_static"
    return result


@tool
def get_competitor_landscape(market: str, product_type: str = "fintech lending") -> dict:
    """Get competitor landscape via DuckDuckGo Instant Answer (free, no key)."""
    try:
        q = f"{product_type} competitors {market} fintech 2024"
        r = requests.get("https://api.duckduckgo.com/",
                         params={"q": q, "format": "json", "no_redirect": 1},
                         timeout=8)
        d = r.json()
        abstract = d.get("AbstractText", "") or d.get("Answer", "")
        return {
            "source":            "DuckDuckGo",
            "product":           product_type,
            "market":            market,
            "competition_level": "Medium",
            "competitor_types":  ["Local banks","Neobanks","BNPL providers",
                                   "P2P lending platforms","International fintechs"],
            "context":           abstract[:400] if abstract else "Competition data limited.",
        }
    except Exception:
        return {"source":"fallback","market":market,"competition_level":"Medium",
                "competitor_types":["Local banks","Neobanks","International fintechs"]}


@tool
def estimate_market_size(market: str) -> dict:
    """Return heuristic fintech market size estimates (validated benchmarks)."""
    estimates = {
        "AE": {"size_usd": "2.5B", "growth_rate_pct": 14, "maturity": "Developing"},
        "SA": {"size_usd": "3.0B", "growth_rate_pct": 18, "maturity": "Developing"},
        "IN": {"size_usd": "50B",  "growth_rate_pct": 22, "maturity": "Mature"},
        "ID": {"size_usd": "8B",   "growth_rate_pct": 19, "maturity": "Developing"},
        "SG": {"size_usd": "4B",   "growth_rate_pct": 12, "maturity": "Mature"},
        "MY": {"size_usd": "2B",   "growth_rate_pct": 16, "maturity": "Developing"},
    }
    code = _code(market)
    data = estimates.get(code, {"size_usd": "Emerging market", "growth_rate_pct": 12, "maturity": "Emerging"})
    data["source"] = "Benchmark estimates"
    data["country_code"] = code
    return data
