import json
import os
import requests
from pathlib import Path
from langchain_core.tools import tool

_KNOWLEDGE_PATH = (
    Path(__file__).resolve().parent.parent.parent / "data" / "ra_groups_knowledge.json"
)
_NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")


def _load_knowledge() -> dict:
    try:
        with open(_KNOWLEDGE_PATH, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"WARNING: Knowledge file not found at {_KNOWLEDGE_PATH}")
        return {}

_KB = _load_knowledge()


@tool
def get_company_profile() -> str:
    """
    Retrieve RA Groups company profile: name, headquarters, core segments, target regions.
    Data source: internal ra_groups_knowledge.json
    """
    profile = _KB.get("company_profile", {})
    if not profile:
        return "Company profile not available."
    return (
        f"Company: {profile.get('name')} | "
        f"Founded: {profile.get('founded_year')} | "
        f"HQ: {profile.get('headquarters')} | "
        f"Description: {profile.get('description','')} | "
        f"Core segments: {', '.join(profile.get('core_segments', []))} | "
        f"Target regions: {', '.join(profile.get('target_regions', []))}"
    )


@tool
def get_strategic_objectives() -> str:
    """
    Retrieve RA Groups 3-year strategic objectives, risk appetite, and priority themes.
    Data source: internal ra_groups_knowledge.json
    """
    obj = _KB.get("strategic_objectives", {})
    if not obj:
        return "Strategic objectives not available."
    objectives = "\n".join(f"  - {o}" for o in obj.get("3_year_objectives", []))
    themes     = ", ".join(obj.get("priority_themes", []))
    return (
        f"Risk appetite: {obj.get('risk_appetite')} | "
        f"Priority themes: {themes}\n"
        f"3-year objectives:\n{objectives}"
    )


@tool
def get_past_expansions(market: str = "") -> str:
    """
    Retrieve RA Groups past market expansion records with ROI and lessons.
    Args:
        market: Optional market name to filter e.g. India. Empty = return all.
    """
    expansions = _KB.get("past_expansions", [])
    if not expansions:
        return "No past expansion records available."

    if market:
        filtered = [e for e in expansions if market.lower() in e.get("market", "").lower()]
        if filtered:
            expansions = filtered

    result = []
    for e in expansions:
        roi     = e.get("2_year_roi_percent")
        roi_str = f"{roi}%" if roi is not None else "TBD"
        lessons = " | ".join(e.get("key_lessons", []))
        invest  = e.get("initial_investment_usd", 0)
        result.append(
            f"Market: {e['market']} ({e['year']}) | "
            f"Segment: {e.get('segment_focus','N/A')} | "
            f"Investment: ${invest:,} | "
            f"Status: {e['status']} | "
            f"2Y ROI: {roi_str} | "
            f"NPL: {e.get('npl_ratio_percent')}% | "
            f"Lessons: {lessons}"
        )
    return "\n".join(result)


@tool
def get_financial_history() -> str:
    """
    Retrieve RA Groups 3-year financial performance: revenue, EBIT margin, loan book, NPL.
    Data source: internal ra_groups_knowledge.json
    """
    history = _KB.get("financial_history", [])
    if not history:
        return "Financial history not available."
    rows = []
    for h in history:
        rows.append(
            f"Year {h['year']}: "
            f"Revenue ${h['total_revenue_usd']:,} | "
            f"EBIT margin {h['ebit_margin_percent']}% | "
            f"Loan book ${h['net_loan_book_usd']:,} | "
            f"NPL {h['npl_ratio_percent']}% | "
            f"{h.get('comment','')}"
        )
    return "RA Groups financials:\n" + "\n".join(rows)


@tool
def get_risk_policies_and_budget() -> str:
    """
    Retrieve RA Groups risk policies, budget limits, team size, tech assets, KPI thresholds.
    Data source: internal ra_groups_knowledge.json
    """
    risk      = _KB.get("risk_policies", {})
    resources = _KB.get("resources", {})
    kpis      = _KB.get("kpi_benchmarks", {})
    products  = _KB.get("product_portfolio", [])

    if not risk:
        return "Risk policies not available."

    credit    = risk.get("credit_risk_guidelines", {})
    limits    = risk.get("concentration_limits", {})
    tech      = resources.get("existing_tech_assets", [])
    prod_names = [p.get("product_name") for p in products]

    return (
        f"Risk appetite: {risk.get('risk_appetite')} | "
        f"Max single market investment: ${risk.get('max_single_market_investment_usd', 0):,} | "
        f"Single country loan book limit: {limits.get('single_country_limit_percent_of_loan_book')}% | "
        f"Target NPL: {credit.get('target_portfolio_npl_ratio_percent')}% | "
        f"Available expansion budget: ${resources.get('available_expansion_budget_usd', 0):,} | "
        f"Engineering: {resources.get('engineering_headcount')} | "
        f"Data science: {resources.get('data_science_headcount')} | "
        f"Credit risk team: {resources.get('credit_risk_team_size')} | "
        f"Min IRR threshold: {kpis.get('target_min_project_irr_percent')}% | "
        f"Min 2Y ROI threshold: {kpis.get('target_min_2_year_roi_percent')}% | "
        f"Max NPL threshold: {kpis.get('max_acceptable_npl_ratio_percent')}% | "
        f"Products: {', '.join(prod_names)} | "
        f"Tech assets: {', '.join(tech)}"
    )


@tool
def search_industry_context(market: str, product_type: str) -> str:
    """
    Fetch live fintech industry context using NewsAPI (if key set) or
    DuckDuckGo Instant Answer (always free, no key needed).
    Enriches internal knowledge with current external signals.
    Args:
        market: Target country e.g. UAE, India
        product_type: Product category e.g. SME lending, fintech
    """
    query = f"fintech regulation {product_type} {market} 2024 2025 expansion"

    if _NEWS_API_KEY:
        try:
            resp = requests.get(
                "https://newsapi.org/v2/everything",
                params={
                    "q":        query,
                    "sortBy":   "relevancy",
                    "pageSize": 4,
                    "language": "en",
                    "apiKey":   _NEWS_API_KEY,
                },
                timeout=10,
            )
            resp.raise_for_status()
            articles = resp.json().get("articles", [])
            if articles:
                lines = [
                    f"[{a.get('source',{}).get('name','?')}] {a.get('title','')}"
                    for a in articles[:3]
                ]
                return "Live industry context:\n" + "\n".join(lines)
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

        parts   = []
        abstract = data.get("AbstractText", "")
        if abstract:
            parts.append(f"Overview: {abstract[:400]}")
        related = [
            r.get("Text", "")
            for r in data.get("RelatedTopics", [])[:3]
            if isinstance(r, dict) and r.get("Text")
        ]
        if related:
            parts.append("Context: " + " | ".join(related))
        if parts:
            return "\n".join(parts)
    except Exception:
        pass

    return (
        f"Industry context for {product_type} in {market}: "
        "Add NEWS_API_KEY to .env for live headlines. "
        "Market shows active regulatory development and digital lending growth."
    )