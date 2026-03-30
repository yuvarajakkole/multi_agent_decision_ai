"""agents/knowledge_agent/tools.py — Tools for reading internal RA Groups data."""

import json
import requests
from pathlib import Path
from langchain_core.tools import tool
from config.settings import DATASET_PATH


def _load_dataset() -> dict:
    """Load and cache the RA Groups knowledge JSON."""
    path = DATASET_PATH
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[knowledge_agent] Failed to load dataset: {e}")
    # Fallback: search for the file
    for p in Path(__file__).resolve().parents:
        candidate = p / "data" / "ra_groups_knowledge.json"
        if candidate.exists():
            try:
                return json.loads(candidate.read_text(encoding="utf-8"))
            except Exception:
                pass
    print("[knowledge_agent] WARNING: ra_groups_knowledge.json not found")
    return {}


@tool
def load_company_profile() -> dict:
    """Return RA Groups company profile: name, description, HQ, core segments, target regions."""
    d = _load_dataset()
    p = d.get("company_profile", {})
    return {
        "source":          "internal_dataset",
        "company_name":    p.get("name", "RA Groups"),
        "description":     p.get("description", ""),
        "headquarters":    p.get("headquarters", "Dubai, UAE"),
        "founded":         p.get("founded_year"),
        "core_segments":   p.get("core_segments", []),
        "target_regions":  p.get("target_regions", []),
    }


@tool
def load_strategic_objectives() -> dict:
    """Return RA Groups 3-year objectives, risk appetite, and strategic priorities."""
    d = _load_dataset()
    s = d.get("strategic_objectives", {})
    return {
        "source":           "internal_dataset",
        "three_year_goals": s.get("3_year_objectives", []),
        "risk_appetite":    s.get("risk_appetite", "Medium"),
        "priority_themes":  s.get("priority_themes", []),
    }


@tool
def load_past_expansions() -> dict:
    """Return ALL past market expansions: market, year, status, ROI, NPL, lessons."""
    d  = _load_dataset()
    ex = d.get("past_expansions", [])
    return {
        "source":      "internal_dataset",
        "expansions":  ex,
        "total":       len(ex),
        "markets":     [e.get("market") for e in ex],
        "successes":   [e for e in ex if e.get("status") in ("Success", "Moderate Success")],
        "failures":    [e for e in ex if e.get("status") == "Failure"],
    }


@tool
def load_financial_health() -> dict:
    """Return revenue history, EBIT margins, NPL ratios, and KPI benchmarks."""
    d = _load_dataset()
    return {
        "source":             "internal_dataset",
        "financial_history":  d.get("financial_history", []),
        "kpi_benchmarks":     d.get("kpi_benchmarks", {}),
        "latest_year":        d.get("financial_history", [{}])[-1] if d.get("financial_history") else {},
    }


@tool
def load_resource_capacity() -> dict:
    """Return available budget, headcount, existing tech assets."""
    d   = _load_dataset()
    res = d.get("resources", {})
    pol = d.get("risk_policies", {})
    return {
        "source":                        "internal_dataset",
        "available_expansion_budget_usd": res.get("available_expansion_budget_usd", 0),
        "max_single_market_investment":  pol.get("max_single_market_investment_usd", 5_000_000),
        "engineering_headcount":         res.get("engineering_headcount", 0),
        "data_science_headcount":        res.get("data_science_headcount", 0),
        "compliance_team_size":          res.get("compliance_team_size", 0),
        "credit_risk_team_size":         res.get("credit_risk_team_size", 0),
        "existing_tech_assets":          res.get("existing_tech_assets", []),
        "preferred_market_profile":      pol.get("preferred_market_profile", []),
        "concentration_limits":          pol.get("concentration_limits", {}),
        "credit_risk_guidelines":        pol.get("credit_risk_guidelines", {}),
    }


@tool
def search_company_context(market: str, product_type: str) -> dict:
    """
    Search DuckDuckGo for external context about RA Groups or similar companies
    in this market with this product.
    """
    queries = [
        f"RA Groups {market} fintech expansion",
        f"{product_type} fintech company expanding to {market} strategy",
        f"fintech lending {market} regulatory requirements 2024",
    ]
    results = []
    for q in queries[:2]:  # limit to 2 queries
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

    context = " | ".join(r["snippet"] for r in results) if results else "No live context available."
    return {
        "source":  "DuckDuckGo",
        "context": context[:600],
        "live":    len(results) > 0,
    }
