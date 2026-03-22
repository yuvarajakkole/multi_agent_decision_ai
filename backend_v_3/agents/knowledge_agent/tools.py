"""
Knowledge Agent Tools — reads ra_groups_knowledge.json + live industry search.
Internal data is authoritative. External search adds live context.
"""
import json, requests
from pathlib import Path
from langchain_core.tools import tool

_DATASET_PATH = Path(__file__).resolve().parents[3] / "data" / "ra_groups_knowledge.json"

def _load() -> dict:
    try:
        return json.loads(_DATASET_PATH.read_text())
    except Exception:
        return {}


@tool
def get_company_profile() -> dict:
    """Return RA Groups company profile from internal dataset."""
    d = _load()
    return {
        "source":        "internal_dataset",
        "company_name":  d.get("company_profile", {}).get("name", "RA Groups"),
        "description":   d.get("company_profile", {}).get("description", ""),
        "headquarters":  d.get("company_profile", {}).get("headquarters", ""),
        "core_segments": d.get("company_profile", {}).get("core_segments", []),
        "target_regions":d.get("company_profile", {}).get("target_regions", []),
    }


@tool
def get_strategic_objectives() -> dict:
    """Return RA Groups 3-year strategic objectives and risk appetite."""
    d = _load()
    so = d.get("strategic_objectives", {})
    return {
        "source":            "internal_dataset",
        "objectives":        so.get("3_year_objectives", []),
        "risk_appetite":     so.get("risk_appetite", "Medium"),
        "priority_themes":   so.get("priority_themes", []),
    }


@tool
def get_past_expansions(market: str = "") -> dict:
    """Return past expansion history, optionally filtered by market."""
    d = _load()
    exps = d.get("past_expansions", [])
    if market:
        exps = [e for e in exps if market.lower() in e.get("market","").lower()] or exps
    return {"source": "internal_dataset", "past_expansions": exps}


@tool
def get_financial_history() -> dict:
    """Return RA Groups historical financials (revenue, EBIT, NPL)."""
    d = _load()
    history = d.get("financial_history", [])
    kpis    = d.get("kpi_benchmarks", {})
    return {
        "source":         "internal_dataset",
        "financial_years": history,
        "kpi_benchmarks":  kpis,
    }


@tool
def get_risk_policies_and_budget() -> dict:
    """Return RA Groups risk policies and available expansion budget."""
    d = _load()
    rp  = d.get("risk_policies", {})
    res = d.get("resources", {})
    return {
        "source":                     "internal_dataset",
        "risk_appetite":              rp.get("risk_appetite","Medium"),
        "max_single_market_usd":      rp.get("max_single_market_investment_usd", 5_000_000),
        "preferred_market_profile":   rp.get("preferred_market_profile",[]),
        "concentration_limits":       rp.get("concentration_limits",{}),
        "credit_risk_guidelines":     rp.get("credit_risk_guidelines",{}),
        "available_expansion_budget_usd": res.get("available_expansion_budget_usd", 3_000_000),
        "engineering_headcount":      res.get("engineering_headcount", 0),
        "data_science_headcount":     res.get("data_science_headcount", 0),
    }


@tool
def search_industry_context(market: str, product_type: str = "fintech lending") -> dict:
    """Live industry context via DuckDuckGo Instant Answer (free, no key)."""
    try:
        q = f"{product_type} market {market} trends 2024 2025"
        r = requests.get("https://api.duckduckgo.com/",
                         params={"q": q, "format": "json", "no_redirect": 1}, timeout=8)
        d = r.json()
        abstract = d.get("AbstractText","") or d.get("Answer","")
        return {"source": "DuckDuckGo", "query": q,
                "context": abstract[:500] if abstract else "No live context available."}
    except Exception:
        return {"source": "fallback", "context": "Industry search unavailable."}
