"""agents/financial_agent/agent.py

Same fix as market agent: track tool confidence directly, return it to graph.py.
Returns (merged_data, calcs, tool_conf, tool_source).
"""

import json
import re
from typing import Optional
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage

from config.llm_config import get_fast_llm
from agents.financial_agent.tools import get_macro_indicators, get_fx_rate, get_sector_sentiment
from agents.financial_agent.prompt import SYSTEM, OUTPUT_INSTRUCTIONS, RETRY_INSTRUCTIONS
from core.calculations.financial import (
    classify_product, get_product_yield, get_net_yield,
    calc_roi, calc_irr, calc_payback_months, score_financials,
)

TOOLS   = [get_macro_indicators, get_fx_rate, get_sector_sentiment]
BY_NAME = {t.name: t for t in TOOLS}


async def run(
    user_query:      str,
    market:          str,
    budget:          float,
    timeline_months: int,
    previous_output: Optional[str] = None,
    quality_issues:  Optional[list] = None,
) -> tuple[dict, dict, float, str]:
    """
    Returns:
        merged_data   – combined LLM + deterministic calcs
        calcs         – deterministic calculations only
        tool_conf     – best confidence from live tools
        tool_source   – source label
    """
    llm = get_fast_llm()
    lwt = llm.bind_tools(TOOLS)

    best_tool_conf   = 0.35   # floor: deterministic calcs always have value
    best_tool_source = "deterministic"

    user_content = (
        RETRY_INSTRUCTIONS.format(
            issues           = ", ".join(quality_issues or []),
            specific_requests= "\n".join(f"- {i}" for i in (quality_issues or [])),
            previous_output  = (previous_output or "")[:600],
        )
        if previous_output and quality_issues
        else (
            f"Query: {user_query}\nMarket: {market}\n"
            f"Budget: ${budget:,.0f}\nTimeline: {timeline_months} months\n\n"
            + OUTPUT_INSTRUCTIONS
        )
    )

    msgs = [SystemMessage(content=SYSTEM), HumanMessage(content=user_content)]
    llm_output = {"_parse_error": True}

    for _ in range(10):
        resp = await lwt.ainvoke(msgs)
        msgs.append(resp)

        if not resp.tool_calls:
            llm_output = _parse_llm(resp.content)
            break

        for tc in resp.tool_calls:
            fn = BY_NAME.get(tc["name"])
            try:
                result = fn.invoke(tc["args"]) if fn else {"error": f"Unknown: {tc['name']}"}
            except Exception as e:
                result = {"error": str(e)}

            # Track best tool confidence directly
            if isinstance(result, dict):
                t_conf   = float(result.get("confidence", 0.0) or 0.0)
                t_source = str(result.get("source", "static"))
                t_ignore = bool(result.get("ignore", True))
                if not t_ignore and t_conf > best_tool_conf:
                    best_tool_conf   = t_conf
                    best_tool_source = t_source

            msgs.append(ToolMessage(
                content      = json.dumps(result) if isinstance(result, (dict, list)) else str(result),
                tool_call_id = tc["id"],
            ))
    else:
        final      = await lwt.ainvoke(msgs)
        llm_output = _parse_llm(final.content)

    # ── Deterministic calculations (code, never LLM) ─────────────────────────
    base_rate  = float(llm_output.get("base_lending_rate_pct") or 8.0)
    ptype      = classify_product(user_query)
    gross      = get_product_yield(base_rate, user_query)
    net        = get_net_yield(gross, user_query)
    yrs        = max(timeline_months / 12, 1.0)
    annual_inc = budget * (net / 100)
    revenue    = budget + annual_inc * yrs
    roi        = calc_roi(revenue, budget)
    irr        = calc_irr(net, user_query, base_rate * 0.60)
    payback    = calc_payback_months(budget, annual_inc / 12)
    risk       = llm_output.get("risk_level", "Medium")
    fin_score  = score_financials(roi, irr, payback, risk, timeline_months)

    calcs = {
        "product_class":           ptype,
        "base_lending_rate_pct":   round(base_rate, 2),
        "product_gross_yield_pct": round(gross, 2),
        "product_net_yield_pct":   round(net, 2),
        "annual_net_income_usd":   round(annual_inc, 0),
        "timeline_years":          round(yrs, 1),
        "estimated_roi_pct":       roi,
        "estimated_irr_pct":       irr,
        "payback_months":          payback,
        "attractiveness_score":    fin_score["score"],
        "financial_attractiveness":fin_score["label"],
        "meets_roi_target":        fin_score["meets_roi_target"],
        "meets_irr_target":        fin_score["meets_irr_target"],
        "annualised_roi":          fin_score["annualised_roi"],
        "roi_gap":                 fin_score["roi_gap"],
        "irr_gap":                 fin_score["irr_gap"],
        "irr_model":               "lending_roe" if ptype == "lending" else "net_yield",
    }

    merged = {**llm_output, **calcs}   # code calcs override any LLM numbers
    return merged, calcs, best_tool_conf, best_tool_source


def _parse_llm(raw: str) -> dict:
    cleaned = raw.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    m = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if m:
        try:
            return json.loads(m.group())
        except Exception:
            pass
    return {"_parse_error": True, "summary": "Financial analysis parse failed."}
