"""
Knowledge Agent Tools — reads ra_groups_knowledge.json + live industry search.
Internal data is authoritative. External search adds live context.

PATH FIX: tools.py lives at backend/agents/knowledge_agent/tools.py
  parents[0] = knowledge_agent/
  parents[1] = agents/
  parents[2] = backend/          ← data/ folder is here
"""
import json, requests
from pathlib import Path
from langchain_core.tools import tool

# Correct path: backend/data/ra_groups_knowledge.json
_DATASET_PATH = Path(__file__).resolve().parents[2] / "data" / "ra_groups_knowledge.json"


def _load() -> dict:
    """Load internal RA Groups dataset. Logs path so user can verify."""
    try:
        data = json.loads(_DATASET_PATH.read_text())
        return data
    except FileNotFoundError:
        print(f"[knowledge_agent] ⚠️  Dataset not found at: {_DATASET_PATH}")
        # Try alternate paths
        for alt in [
            Path(__file__).resolve().parents[3] / "data" / "ra_groups_knowledge.json",
            Path(__file__).resolve().parents[2] / "ra_groups_knowledge.json",
        ]:
            if alt.exists():
                print(f"[knowledge_agent] Found at alternate path: {alt}")
                return json.loads(alt.read_text())
        return {}
    except Exception as e:
        print(f"[knowledge_agent] ⚠️  Dataset load error: {e}")
        return {}


@tool
def get_company_profile() -> dict:
    """Return RA Groups company profile from the internal dataset."""
    d = _load()
    profile = d.get("company_profile", {})
    return {
        "source":         "internal_dataset",
        "company_name":   profile.get("name", "RA Groups"),
        "description":    profile.get("description", ""),
        "headquarters":   profile.get("headquarters", "Dubai, UAE"),
        "founded_year":   profile.get("founded_year", ""),
        "core_segments":  profile.get("core_segments", []),
        "target_regions": profile.get("target_regions", []),
    }


@tool
def get_strategic_objectives() -> dict:
    """Return RA Groups 3-year strategic objectives and risk appetite from internal dataset."""
    d  = _load()
    so = d.get("strategic_objectives", {})
    return {
        "source":            "internal_dataset",
        "objectives":        so.get("3_year_objectives", []),
        "risk_appetite":     so.get("risk_appetite", "Medium"),
        "priority_themes":   so.get("priority_themes", []),
    }


@tool
def get_past_expansions(market: str = "") -> dict:
    """
    Return RA Groups past expansion history from internal dataset.
    Optionally filter by market name.
    """
    d    = _load()
    exps = d.get("past_expansions", [])

    # Filter by market if provided, but fall back to all if none match
    if market:
        filtered = [e for e in exps if market.lower() in e.get("market", "").lower()]
        exps     = filtered if filtered else exps

    return {
        "source":           "internal_dataset",
        "past_expansions":  exps,
        "total_expansions": len(exps),
    }


@tool
def get_financial_history() -> dict:
    """Return RA Groups historical financials (revenue, EBIT, NPL) from internal dataset."""
    d       = _load()
    history = d.get("financial_history", [])
    kpis    = d.get("kpi_benchmarks", {})
    return {
        "source":          "internal_dataset",
        "financial_years": history,
        "kpi_benchmarks":  kpis,
        "latest_year":     history[-1] if history else {},
    }


@tool
def get_risk_policies_and_budget() -> dict:
    """Return RA Groups risk policies and available expansion budget from internal dataset."""
    d   = _load()
    rp  = d.get("risk_policies", {})
    res = d.get("resources", {})
    return {
        "source":                         "internal_dataset",
        "risk_appetite":                  rp.get("risk_appetite", "Medium"),
        "max_single_market_usd":          rp.get("max_single_market_investment_usd", 5_000_000),
        "preferred_market_profile":       rp.get("preferred_market_profile", []),
        "concentration_limits":           rp.get("concentration_limits", {}),
        "credit_risk_guidelines":         rp.get("credit_risk_guidelines", {}),
        "available_expansion_budget_usd": res.get("available_expansion_budget_usd", 3_000_000),
        "engineering_headcount":          res.get("engineering_headcount", 0),
        "data_science_headcount":         res.get("data_science_headcount", 0),
        "compliance_team_size":           res.get("compliance_team_size", 0),
        "existing_tech_assets":           res.get("existing_tech_assets", []),
    }


@tool
def get_product_portfolio() -> dict:
    """Return RA Groups product portfolio from internal dataset."""
    d        = _load()
    products = d.get("product_portfolio", [])
    return {
        "source":    "internal_dataset",
        "products":  products,
        "count":     len(products),
    }


@tool
def search_industry_context(market: str, product_type: str = "fintech lending") -> dict:
    """Live industry context via DuckDuckGo Instant Answer (free, no key required)."""
    try:
        q = f"{product_type} market {market} trends growth 2024 2025"
        r = requests.get(
            "https://api.duckduckgo.com/",
            params={"q": q, "format": "json", "no_redirect": 1},
            timeout=8,
        )
        d        = r.json()
        abstract = d.get("AbstractText", "") or d.get("Answer", "")
        return {
            "source":  "DuckDuckGo",
            "query":   q,
            "context": abstract[:600] if abstract else "No live context available.",
        }
    except Exception:
        return {"source": "fallback", "context": "Industry search unavailable."}
