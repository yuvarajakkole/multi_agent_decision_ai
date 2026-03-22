"""
Financial Agent Node — deterministic metrics + validated envelope.
ROI/IRR computed by financial.py. LLM only interprets qualitative context.
Handles both lending and non-lending product types correctly.
"""
import json, re, requests
from agents.financial_agent.agent import run_financial_agent
from core.calculations.financial import (
    calculate_roi,
    calculate_irr_lending_book,
    calculate_payback_months,
    calculate_product_yield,
    calculate_net_yield,
    score_financial_attractiveness,
    classify_product,
)
from core.reliability.validator import validate_agent_output
from core.reliability.fallback import get_fallback_macro, _CODES
from core.trace.decision_trace import compact_input, compact_output
from streaming.agent_step_streamer import stream_agent_start, stream_agent_complete


def _get_lending_rate(market: str) -> tuple:
    code = _CODES.get(market.lower().strip(), market[:2].upper())
    try:
        url = (f"https://api.worldbank.org/v2/country/{code}"
               f"/indicator/FR.INR.LEND?format=json&mrv=3&per_page=3")
        d = requests.get(url, timeout=10).json()
        if len(d) > 1 and d[1]:
            for e in d[1]:
                if e.get("value") is not None:
                    return float(e["value"]), "World Bank API"
    except Exception:
        pass
    fb = get_fallback_macro(market)
    return fb["lending_rate"], "fallback_static"


def _parse(raw: str) -> dict:
    try:
        return json.loads(raw.strip().replace("```json","").replace("```","").strip())
    except Exception:
        pass
    m = re.search(r"\{.*\}", raw, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except Exception:
            pass
    return {}


async def financial_agent_node(state: dict) -> dict:
    print("\n========== FINANCIAL AGENT NODE START ==========")
    request_id      = state["request_id"]
    user_query      = state["user_query"]
    market          = state.get("market", "unknown")
    budget          = float(state.get("budget", 1_000_000))
    timeline_months = int(state.get("timeline_months", 12))
    trace           = state.get("_trace")

    if trace:
        trace.start_step("financial_agent")
    await stream_agent_start(request_id, "financial_agent")

    # Step 1: LLM + tools gather qualitative context
    raw = await run_financial_agent(
        f"Financial feasibility:\nQuery: {user_query}\n"
        f"Market: {market}\nBudget: ${budget:,.0f}\n"
        f"Timeline: {timeline_months} months\nUse ALL tools. Return JSON."
    )
    llm_data    = _parse(raw)
    data_source = "hybrid" if llm_data else "fallback"

    # Step 2: Deterministic calculations
    product_type = user_query   # full query used for product classification
    ptype        = classify_product(product_type)

    base_rate, rate_src = _get_lending_rate(market)
    gross_yield         = calculate_product_yield(base_rate, product_type)
    net_yield           = calculate_net_yield(gross_yield, product_type=product_type)
    net_yield_decimal   = net_yield / 100.0

    years       = max(timeline_months / 12, 1.0)
    annual_cash = budget * net_yield_decimal
    estimated_rev = budget + annual_cash * years

    roi = calculate_roi(estimated_rev, budget)

    # IRR model depends on product type
    if ptype == "lending":
        try:
            cost_of_funds = float(llm_data.get("lending_rate_percent", base_rate)) * 0.6
        except (TypeError, ValueError):
            cost_of_funds = base_rate * 0.6
        cost_of_funds = max(2.0, min(cost_of_funds, 15.0))
        irr = calculate_irr_lending_book(net_yield, cost_of_funds, 0.60)
    else:
        # For SaaS/tech: IRR ≈ annualised net yield (capital invested, not revolved)
        irr = round(net_yield, 2)

    payback = calculate_payback_months(budget, annual_cash / 12)
    risk_level = llm_data.get("risk_level", "Medium") if llm_data else "Medium"
    attractiveness = score_financial_attractiveness(
        roi, irr, payback, risk_level, timeline_months
    )

    analysis = {
        "market":                   market,
        "product_type_detected":    ptype,
        "data_source":              data_source,
        "lending_rate_source":      rate_src,
        "base_lending_rate_pct":    round(base_rate, 2),
        "product_yield_pct":        round(gross_yield, 2),
        "net_yield_pct":            round(net_yield, 2),
        "annual_net_income_usd":    round(annual_cash, 0),
        "timeline_years":           round(years, 1),
        # Deterministic — NOT LLM-generated
        "estimated_roi_percent":    roi,
        "estimated_irr_percent":    irr,
        "payback_period_months":    payback,
        "meets_roi_threshold":      attractiveness["meets_roi_threshold"],
        "meets_irr_threshold":      attractiveness["meets_irr_threshold"],
        "attractiveness_score":     attractiveness["score"],
        "financial_attractiveness": attractiveness["label"],
        "irr_model":                "lending_book_roe" if ptype == "lending" else "net_yield_proxy",
        # Qualitative from LLM + tools
        "risk_level":               risk_level,
        "risk_factors":             llm_data.get("risk_factors", []),
        "currency":                 llm_data.get("currency", "N/A"),
        "exchange_rate_to_usd":     llm_data.get("exchange_rate_to_usd", "N/A"),
        "currency_stability":       llm_data.get("currency_stability", "N/A"),
        "inflation_percent":        llm_data.get("inflation_percent", "N/A"),
        "gdp_growth_percent":       llm_data.get("gdp_growth_percent", "N/A"),
        "stock_index_performance":  llm_data.get("stock_index_performance", "N/A"),
        "fintech_etf_sentiment":    llm_data.get("fintech_etf_sentiment", "N/A"),
        "summary":                  llm_data.get("summary", "Financial analysis completed."),
    }

    envelope = validate_agent_output(
        "financial_agent", "financial_analysis", analysis, data_source
    )
    print(f"Financial confidence: {envelope['confidence']} | Errors: {envelope['errors']}")
    if envelope.get("warnings"):
        print(f"Warnings: {envelope['warnings'][:2]}")

    if trace:
        trace.log_step(
            "financial_agent", compact_input(state), compact_output(analysis),
            envelope["confidence"], data_source,
            envelope["errors"], envelope["warnings"],
        )

    await stream_agent_complete(request_id, "financial_agent", {
        "roi": roi, "irr": irr, "payback_months": payback,
        "product_type": ptype,
        "confidence": envelope["confidence"],
        "attractiveness": attractiveness["label"],
    })
    print("========== FINANCIAL AGENT NODE END ==========\n")
    return {"financial_analysis": analysis, "_financial_agent_envelope": envelope}
