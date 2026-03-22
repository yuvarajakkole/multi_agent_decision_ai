import json, re, requests
from agents.financial_agent.agent import run_financial_agent
from core.calculations.financial import (
    classify_product, calculate_product_yield, calculate_net_yield,
    calculate_irr, calculate_roi, calculate_payback_months, score_financial_attractiveness,
)
from core.reliability.validator import validate_agent_output
from core.reliability.fallback import get_fallback_macro, code as _code
from core.trace.decision_trace import compact_input, compact_output
from streaming.agent_step_streamer import stream_agent_start, stream_agent_complete

def _get_rate(market):
    c=_code(market)
    try:
        r=requests.get(f"https://api.worldbank.org/v2/country/{c}/indicator/FR.INR.LEND?format=json&mrv=3&per_page=3",timeout=10)
        d=r.json()
        if len(d)>1 and d[1]:
            for e in d[1]:
                if e.get("value") is not None: return float(e["value"]),"World Bank"
    except: pass
    return get_fallback_macro(market)["lending_rate"],"fallback"

def _parse(raw):
    try: return json.loads(raw.strip().replace("```json","").replace("```","").strip())
    except: pass
    m=re.search(r"\{.*\}",raw,re.DOTALL)
    if m:
        try: return json.loads(m.group())
        except: pass
    return {}

async def financial_agent_node(state: dict) -> dict:
    print("\n========== FINANCIAL AGENT NODE START ==========")
    rid=state["request_id"]; uq=state["user_query"]; market=state.get("market","unknown")
    budget=float(state.get("budget",1_000_000)); tl=int(state.get("timeline_months",12))
    trace=state.get("_trace")
    if trace: trace.start_step("financial_agent")
    await stream_agent_start(rid,"financial_agent")

    raw = await run_financial_agent(
        f"Query: {uq}\nMarket: {market}\nBudget: ${budget:,.0f}\nTimeline: {tl} months\n"
        "Use ALL tools. Return JSON.")
    llm = _parse(raw); src="hybrid" if llm else "fallback"

    base_rate, rate_src = _get_rate(market)
    ptype = classify_product(uq)
    gross = calculate_product_yield(base_rate, uq)
    net   = calculate_net_yield(gross, uq)
    net_d = net/100.0; yrs=max(tl/12,1.0)
    annual= budget*net_d; rev=budget+annual*yrs
    roi   = calculate_roi(rev, budget)
    irr   = calculate_irr(net, uq, base_rate*0.60 if ptype=="lending" else 4.0)
    pb    = calculate_payback_months(budget, annual/12)
    risk  = llm.get("risk_level","Medium") if llm else "Medium"
    score = score_financial_attractiveness(roi,irr,pb,risk,tl)

    analysis = {
        "market":market,"product_type":ptype,"data_source":src,"lending_rate_source":rate_src,
        "base_lending_rate_pct":round(base_rate,2),"product_yield_pct":round(gross,2),
        "net_yield_pct":round(net,2),"annual_net_income_usd":round(annual,0),"timeline_years":round(yrs,1),
        "estimated_roi_percent":roi,"estimated_irr_percent":irr,"payback_period_months":pb,
        "meets_roi_threshold":score["meets_roi_threshold"],"meets_irr_threshold":score["meets_irr_threshold"],
        "attractiveness_score":score["score"],"financial_attractiveness":score["label"],
        "irr_model":"lending_roe" if ptype=="lending" else "net_yield_proxy",
        "risk_level":risk,"risk_factors":llm.get("risk_factors",[]),
        "currency":llm.get("currency","N/A"),"exchange_rate_to_usd":llm.get("exchange_rate_to_usd","N/A"),
        "currency_stability":llm.get("currency_stability","N/A"),
        "inflation_percent":llm.get("inflation_percent","N/A"),
        "gdp_growth_percent":llm.get("gdp_growth_percent","N/A"),
        "market_sentiment":llm.get("market_sentiment","N/A"),
        "macro_environment":llm.get("macro_environment","N/A"),
        "summary":llm.get("summary","Financial analysis complete."),
    }
    envelope=validate_agent_output("financial_agent","financial_analysis",analysis,src)
    print(f"Financial confidence: {envelope['confidence']} | ROI:{roi}% IRR:{irr}% PB:{pb}mo | Errors:{envelope['errors']}")
    if envelope.get("warnings"): print(f"  Warnings: {envelope['warnings'][:2]}")
    if trace: trace.log_step("financial_agent",compact_input(state),compact_output(analysis),
        envelope["confidence"],src,envelope["errors"],envelope["warnings"])
    await stream_agent_complete(rid,"financial_agent",{
        "roi":roi,"irr":irr,"payback_months":pb,"product_type":ptype,
        "financial_attractiveness":score["label"],"confidence":envelope["confidence"]})
    print("========== FINANCIAL AGENT NODE END ==========\n")
    return {"financial_analysis":analysis,"_financial_agent_envelope":envelope}
