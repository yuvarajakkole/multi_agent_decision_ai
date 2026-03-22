import json, requests
from pathlib import Path
from langchain_core.tools import tool

_PATHS=[
    Path(__file__).resolve().parents[2]/"data"/"ra_groups_knowledge.json",
    Path(__file__).resolve().parents[3]/"data"/"ra_groups_knowledge.json",
    Path(__file__).resolve().parents[2]/"ra_groups_knowledge.json",
]
def _load():
    for p in _PATHS:
        if p.exists():
            try: return json.loads(p.read_text(encoding="utf-8"))
            except: pass
    print("[knowledge_agent] WARNING: ra_groups_knowledge.json not found in any expected path")
    return {}

@tool
def get_company_profile() -> dict:
    "Return RA Groups company profile."
    d=_load(); p=d.get("company_profile",{})
    return {"source":"internal","company_name":p.get("name","RA Groups"),
        "description":p.get("description",""),"headquarters":p.get("headquarters",""),
        "core_segments":p.get("core_segments",[]),"target_regions":p.get("target_regions",[])}

@tool
def get_strategic_objectives() -> dict:
    "Return RA Groups strategic objectives and risk appetite."
    d=_load(); s=d.get("strategic_objectives",{})
    return {"source":"internal","objectives":s.get("3_year_objectives",[]),
        "risk_appetite":s.get("risk_appetite","Medium"),"priority_themes":s.get("priority_themes",[])}

@tool
def get_all_past_expansions() -> dict:
    "Return ALL past expansions with outcomes, ROI, and lessons."
    d=_load(); e=d.get("past_expansions",[])
    return {"source":"internal","past_expansions":e,"total":len(e),
        "markets":[x.get("market") for x in e],
        "successful":[x for x in e if x.get("status") in ("Success","Moderate Success")]}

@tool
def get_financial_history_and_kpis() -> dict:
    "Return revenue history, EBIT margins, NPL ratios, KPI benchmarks."
    d=_load()
    return {"source":"internal","financial_history":d.get("financial_history",[]),
        "kpi_benchmarks":d.get("kpi_benchmarks",{}),"resources":d.get("resources",{})}

@tool
def get_risk_policy_and_budget() -> dict:
    "Return risk policies, concentration limits, available budget."
    d=_load(); r=d.get("risk_policies",{}); res=d.get("resources",{})
    return {"source":"internal","risk_appetite":r.get("risk_appetite","Medium"),
        "max_single_market_usd":r.get("max_single_market_investment_usd",5_000_000),
        "preferred_market_profile":r.get("preferred_market_profile",[]),
        "concentration_limits":r.get("concentration_limits",{}),
        "credit_risk_guidelines":r.get("credit_risk_guidelines",{}),
        "available_budget_usd":res.get("available_expansion_budget_usd",3_000_000),
        "engineering_hc":res.get("engineering_headcount",0),
        "data_science_hc":res.get("data_science_headcount",0),
        "existing_tech_assets":res.get("existing_tech_assets",[])}

@tool
def get_product_portfolio() -> dict:
    "Return existing products with IRR, NPL, and target customers."
    d=_load(); p=d.get("product_portfolio",[])
    return {"source":"internal","products":p,"count":len(p)}

@tool
def search_industry_context(market: str, product_type: str) -> dict:
    "Live DuckDuckGo search for industry context."
    try:
        q=f"{product_type} {market} industry 2024 2025 opportunity challenge"
        r=requests.get("https://api.duckduckgo.com/",
            params={"q":q,"format":"json","no_redirect":1},timeout=8)
        d=r.json(); text=d.get("AbstractText","") or d.get("Answer","")
        return {"source":"DuckDuckGo","query":q,"context":text[:500] if text else "No live context."}
    except: return {"source":"fallback","context":"Search unavailable."}
