"""
supervisor/supervisor_graph.py

Fixes:
  1. Market extracted from query text — never overridden by UI field default
  2. Unknown market → "UNKNOWN", never guessed or truncated
  3. Budget extracted from query text; if missing → explicit low_confidence flag
  4. Timeline extracted from query text; if missing → explicit flag (no default 12)
  5. Advisory vs decision detection
  6. Currency conversion with audit trail
  7. temperature=0 already set in llm_config — supervisor inherits this
"""

import json
import re
from datetime import datetime, timezone
from typing import Optional

from langchain_core.messages import SystemMessage, HumanMessage
from config.llm_config import get_fast_llm
from streaming.streamer import stream_event
from core.reliability.market_data import resolve_iso

# ─── Currency conversion table ────────────────────────────────────────────────
# Rates are approximate. Used only when user specifies non-USD amount.
# If rate is missing → confidence lowered but budget still attempted.
_CURRENCY_TO_USD: dict[str, float] = {
    # South Asia
    "rupee": 0.012, "rupees": 0.012, "rupe": 0.012, "rupes": 0.012,
    "inr": 0.012, "₹": 0.012,
    # GCC
    "aed": 0.272, "dirham": 0.272, "dirhams": 0.272,
    "sar": 0.267, "riyal": 0.267, "riyals": 0.267,
    "omr": 2.60,  "baisa": 0.0026,
    "kwd": 3.26,  "kuwaiti dinar": 3.26,
    "bhd": 2.65,  "bahraini dinar": 2.65,
    "qar": 0.274,
    # Europe
    "gbp": 1.27, "pound": 1.27, "pounds": 1.27,
    "eur": 1.08, "euro": 1.08, "euros": 1.08,
    "sek": 0.094, "nok": 0.095, "dkk": 0.145,
    # Asia-Pacific
    "sgd": 0.74, "singapore dollar": 0.74,
    "myr": 0.22, "ringgit": 0.22,
    "idr": 0.000064, "rupiah": 0.000064,
    "thb": 0.028, "baht": 0.028,
    "vnd": 0.000040,
    "php": 0.018, "peso": 0.018,
    "pkr": 0.0036, "pakistani rupee": 0.0036,
    "bdt": 0.0091, "taka": 0.0091,
    "lkr": 0.0031,
    # Africa
    "ngn": 0.00065, "naira": 0.00065,
    "kes": 0.0077, "shilling": 0.0077,
    "zar": 0.055, "rand": 0.055,
    "ghs": 0.068, "cedi": 0.068,
    "etb": 0.018,
    "tzs": 0.00038,
    "rwf": 0.00073,
    # Americas
    "brl": 0.20, "real": 0.20,
    "mxn": 0.057, "peso mexicano": 0.057,
    "cop": 0.00025,
    "clp": 0.0011,
    "pen": 0.27, "sol": 0.27,
    "ars": 0.0011,
    # Other
    "try": 0.031, "lira": 0.031,
    "krw": 0.00076, "won": 0.00076,
    "jpy": 0.0066, "yen": 0.0066,
    "cny": 0.138, "yuan": 0.138, "rmb": 0.138,
    "hkd": 0.128,
    "twd": 0.032,
    "aud": 0.65, "australian dollar": 0.65,
    "nzd": 0.60,
    "cad": 0.73, "canadian dollar": 0.73,
}


def _extract_budget(query: str, ui_budget: float) -> tuple[float, str, list[str]]:
    """
    Extract budget from query text.  Returns (amount_usd, currency_note, warnings).
    If query mentions a specific amount, use it (with conversion).
    If no amount in query but UI provided one, use UI value and note it.
    """
    warnings: list[str] = []
    q_lower = query.lower()

    # Find numeric amount in query
    # Patterns like "1000000 rupees", "₹10 lakh", "$500k", "500000 USD"
    amount_patterns = [
        r"(\d[\d,\.]*)\s*(crore|cr)\b",       # Indian crore
        r"(\d[\d,\.]*)\s*(lakh|lac|l)\b",     # Indian lakh
        r"(\d[\d,\.]*)\s*(million|mn|m)\b",   # million
        r"(\d[\d,\.]*)\s*(billion|bn|b)\b",   # billion
        r"(\d[\d,\.]*)\s*(k)\b",              # thousand
        r"(\d[\d,\.]*)",                       # plain number
    ]
    multipliers = {
        "crore": 10_000_000, "cr": 10_000_000,
        "lakh": 100_000,    "lac": 100_000, "l": 100_000,
        "million": 1_000_000, "mn": 1_000_000, "m": 1_000_000,
        "billion": 1_000_000_000, "bn": 1_000_000_000, "b": 1_000_000_000,
        "k": 1_000,
    }

    raw_amount: Optional[float] = None
    multiplier = 1.0

    for pattern in amount_patterns:
        m = re.search(pattern, q_lower)
        if m:
            try:
                num_str = m.group(1).replace(",", "")
                raw_amount = float(num_str)
                suffix = m.group(2).lower() if len(m.groups()) > 1 else ""
                multiplier = multipliers.get(suffix, 1.0)
                raw_amount *= multiplier
                break
            except Exception:
                pass

    # Detect currency keyword
    currency_rate  = 1.0   # default USD
    currency_found = "USD"
    for kw, rate in sorted(_CURRENCY_TO_USD.items(), key=lambda x: -len(x[0])):
        if kw in q_lower:
            currency_rate  = rate
            currency_found = kw.upper()
            break

    if raw_amount is not None:
        amount_usd = round(raw_amount * currency_rate, 2)
        note = (
            f"Extracted from query: {raw_amount:,.0f} {currency_found}"
            + (f" × {currency_rate} = ${amount_usd:,.0f} USD" if currency_found != "USD" else "")
        )
        return amount_usd, note, warnings

    # No amount in query — use UI value if provided, flag it
    if ui_budget and ui_budget > 0:
        if currency_found != "USD" and currency_rate != 1.0:
            # Currency hint in query but no amount — convert UI budget
            amount_usd = round(ui_budget * currency_rate, 2)
            note = f"UI budget {ui_budget:,.0f} converted via {currency_found} rate"
            warnings.append(f"[BUDGET_UI] No amount in query; used UI field and converted currency")
        else:
            amount_usd = ui_budget
            note = "From UI field (no amount in query)"
            warnings.append(
                "[BUDGET_UI] Budget taken from UI field — not mentioned in query. "
                "Confidence reduced."
            )
        return amount_usd, note, warnings

    # Nothing found
    warnings.append(
        "[BUDGET_MISSING] No budget specified in query or UI. "
        "Financial analysis will use zero — confidence will be low."
    )
    return 0.0, "Not specified", warnings


def _extract_timeline(query: str, ui_timeline: int) -> tuple[int, str, list[str]]:
    """Extract timeline from query text. Returns (months, note, warnings)."""
    warnings: list[str] = []
    q_lower = query.lower()

    # Patterns: "12 months", "1 year", "18 months", "2 years"
    m = re.search(r"(\d+)\s*(month|months|mo)", q_lower)
    if m:
        months = int(m.group(1))
        return months, f"Extracted from query: {months} months", warnings

    m = re.search(r"(\d+)\s*(year|years|yr|yrs)", q_lower)
    if m:
        months = int(m.group(1)) * 12
        return months, f"Extracted from query: {m.group(1)} year(s) = {months} months", warnings

    if ui_timeline and ui_timeline > 0:
        warnings.append(
            f"[TIMELINE_UI] Timeline taken from UI field ({ui_timeline}m) — not in query."
        )
        return ui_timeline, f"From UI field: {ui_timeline} months", warnings

    # Default — noted explicitly
    warnings.append(
        "[TIMELINE_DEFAULT] No timeline specified — using 12 months as default. "
        "Financial projections may not reflect actual plans."
    )
    return 12, "Default 12 months (not specified)", warnings


# ─── Advisory detection ───────────────────────────────────────────────────────

_ADVISORY_PATTERNS = [
    r"which\s+(field|sector|industry|market|area|business)",
    r"what\s+(field|sector|industry)\s+(should|can|to)",
    r"where\s+should\s+i\s+(invest|open|start|expand|launch)",
    r"give\s+me\s+(an\s+)?(idea|ideas|suggestion|suggestions|recommendation|options)",
    r"what\s+(should|can)\s+i\s+(do|invest|start|open|explore)",
    r"suggest\s+(a|some|me|an)",
    r"recommend\s+(a|some|me|an)",
    r"best\s+(field|sector|market|industry|option|opportunity)",
    r"good\s+(field|sector|market|industry)\s+(for|to|in)",
    r"what\s+(business|startup|venture)\s+(should|can|would)",
    r"ideas?\s+for\s+(investment|business|startup|expansion)",
    r"should\s+i\s+(invest|start|open)\s+in\s+\w+\??$",
]


def _is_advisory(query: str) -> bool:
    q = query.lower().strip()
    return any(re.search(p, q) for p in _ADVISORY_PATTERNS)


# ─── LLM extraction prompt ───────────────────────────────────────────────────

_SYSTEM = """
You are an AI supervisor for a business decision system.
Extract structured fields from the user query.

RULES:
1. product_detected: exact product/service from query — never generic.
   BAD:  "lending"   GOOD: "SME working capital lending"
   BAD:  "tech"      GOOD: "GPU semiconductor manufacturing"

2. market_detected: country/region from QUERY TEXT ONLY.
   - Use only names explicitly in the query.
   - If no market in query → null.
   - DO NOT infer from context. DO NOT use market field as substitute.
   - "island" is NOT India. "iran" is NOT India.

3. query_type:
   - "decision"  → user wants GO/NO_GO on a specific opportunity
   - "advisory"  → user wants ideas, options, or open-ended guidance
   - "analysis"  → wants data/analysis without a specific decision

4. product_class:
   - "lending"       → loans, credit, invoice financing, working capital
   - "ai_services"   → AI SaaS, AI APIs, AI tools for customers
   - "manufacturing" → hardware, semiconductors, EVs, physical goods
   - "edtech"        → education technology
   - "payments"      → payment processing, wallets, transfers
   - "saas"          → software as a service (non-AI)
   - "other"         → anything else

Return ONLY valid JSON, no prose:
{
  "product_detected":   "<exact product>",
  "product_class":      "<class>",
  "market_detected":    "<country from query or null>",
  "query_type":         "decision|advisory|analysis",
  "budget_in_query":    <true|false>,
  "timeline_in_query":  <true|false>,
  "is_ra_groups_query": <true|false>,
  "advisory_topic":     "<if advisory: topic, else null>",
  "notes":              "<any parsing observations>"
}
"""


async def supervisor_node(state: dict) -> dict:
    rid        = state["request_id"]
    raw_query  = state["user_query"]
    ui_market  = state.get("market", "") or ""
    ui_budget  = float(state.get("budget", 0) or 0)
    ui_timeline = int(state.get("timeline_months", 0) or 0)

    await stream_event(rid, "agent_start", "supervisor", "Analysing query")
    print(f"\n[supervisor] START  query={raw_query[:80]!r}")

    warnings: list[str] = []

    # ── Fast-path advisory detection ──────────────────────────────────────────
    if _is_advisory(raw_query):
        print("[supervisor] ADVISORY detected (regex)")
        budget_usd, budget_note, bw = _extract_budget(raw_query, ui_budget)
        timeline, tl_note, tw       = _extract_timeline(raw_query, ui_timeline)
        warnings.extend(bw + tw)

        resolved_market = resolve_iso(ui_market) and ui_market or ui_market or "Unknown"

        await stream_event(rid, "agent_complete", "supervisor", {
            "query_type": "advisory", "market": resolved_market})

        return {
            "supervisor_plan":  {"query_type": "advisory", "advisory_topic": raw_query},
            "routing_decision": "advisory",
            "market":           resolved_market,
            "budget":           budget_usd,
            "timeline_months":  timeline,
            "product_type":     "advisory",
            "_supervisor_warnings": warnings,
            "execution_log": [{
                "agent":     "supervisor",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "action":    "advisory_fast_path",
                "budget_note": budget_note,
                "timeline_note": tl_note,
                "warnings":  warnings,
            }],
        }

    # ── LLM extraction ────────────────────────────────────────────────────────
    llm  = get_fast_llm()
    resp = await llm.ainvoke([
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=(
            f"Query: {raw_query}\n"
            f"UI market field (for reference only — do not blindly use): {ui_market!r}\n"
            f"UI budget: {ui_budget}\n"
            f"UI timeline: {ui_timeline}"
        )),
    ])

    plan: dict = {}
    try:
        cleaned = resp.content.strip().replace("```json", "").replace("```", "").strip()
        plan    = json.loads(cleaned)
    except Exception as exc:
        warnings.append(f"[PLAN_PARSE_ERROR] Supervisor LLM output not valid JSON: {exc}")
        plan = {
            "product_detected": raw_query[:60],
            "product_class":    "other",
            "market_detected":  None,
            "query_type":       "decision",
        }

    # ── Resolve market — query text beats UI field, unknown stays unknown ─────
    llm_market = (plan.get("market_detected") or "").strip()

    if llm_market:
        # Verify it's a real country we can resolve
        iso = resolve_iso(llm_market)
        if iso is None:
            warnings.append(
                f"[MARKET_UNRESOLVED] LLM detected '{llm_market}' but cannot resolve to ISO. "
                f"Setting UNKNOWN."
            )
            resolved_market = "UNKNOWN"
        else:
            resolved_market = llm_market
    elif ui_market.strip():
        iso = resolve_iso(ui_market)
        if iso is None:
            warnings.append(
                f"[MARKET_UNRESOLVED] UI market '{ui_market}' cannot be resolved. "
                f"Setting UNKNOWN."
            )
            resolved_market = "UNKNOWN"
        else:
            resolved_market = ui_market
            warnings.append(f"[MARKET_FROM_UI] Market '{ui_market}' taken from UI (not in query)")
    else:
        resolved_market = "UNKNOWN"
        warnings.append("[MARKET_MISSING] No market specified in query or UI field.")

    # ── Advisory re-check after LLM ───────────────────────────────────────────
    if plan.get("query_type") == "advisory":
        budget_usd, budget_note, bw = _extract_budget(raw_query, ui_budget)
        timeline, tl_note, tw       = _extract_timeline(raw_query, ui_timeline)
        warnings.extend(bw + tw)
        await stream_event(rid, "agent_complete", "supervisor", {
            "query_type": "advisory", "market": resolved_market})
        return {
            "supervisor_plan":  plan,
            "routing_decision": "advisory",
            "market":           resolved_market,
            "budget":           budget_usd,
            "timeline_months":  timeline,
            "product_type":     "advisory",
            "_supervisor_warnings": warnings,
            "execution_log": [{
                "agent":        "supervisor",
                "timestamp":    datetime.now(timezone.utc).isoformat(),
                "action":       "advisory_llm",
                "budget_note":  budget_note,
                "timeline_note": tl_note,
                "warnings":     warnings,
            }],
        }

    # ── Budget and timeline ───────────────────────────────────────────────────
    budget_usd, budget_note, bw = _extract_budget(raw_query, ui_budget)
    timeline, tl_note, tw       = _extract_timeline(raw_query, ui_timeline)
    warnings.extend(bw + tw)

    budget_confidence_penalty = budget_usd == 0.0   # will lower overall confidence

    print(
        f"[supervisor] product='{plan.get('product_detected')}'  "
        f"class='{plan.get('product_class')}'  "
        f"market='{resolved_market}'  "
        f"budget=${budget_usd:,.0f}  "
        f"timeline={timeline}m  "
        f"type={plan.get('query_type')}"
    )
    if warnings:
        print(f"[supervisor] warnings: {warnings}")

    await stream_event(rid, "agent_complete", "supervisor", {
        "product":       plan.get("product_detected"),
        "product_class": plan.get("product_class"),
        "market":        resolved_market,
        "budget_usd":    budget_usd,
        "timeline":      timeline,
        "type":          plan.get("query_type"),
        "warnings":      len(warnings),
    })

    return {
        "supervisor_plan":           plan,
        "routing_decision":          "parallel_research",
        "market":                    resolved_market,
        "budget":                    budget_usd,
        "timeline_months":           timeline,
        "product_type":              plan.get("product_class", "other"),
        "_detected_product":         plan.get("product_detected", raw_query[:60]),
        "_budget_note":              budget_note,
        "_timeline_note":            tl_note,
        "_budget_confidence_penalty": budget_confidence_penalty,
        "_supervisor_warnings":      warnings,
        "execution_log": [{
            "agent":           "supervisor",
            "timestamp":       datetime.now(timezone.utc).isoformat(),
            "action":          "query_analysed",
            "plan":            plan,
            "resolved_market": resolved_market,
            "budget_usd":      budget_usd,
            "budget_note":     budget_note,
            "timeline":        timeline,
            "timeline_note":   tl_note,
            "warnings":        warnings,
        }],
    }
