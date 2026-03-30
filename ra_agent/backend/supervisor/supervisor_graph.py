"""
supervisor/supervisor_graph.py

Supervisor node — runs first, extracts real product/market from query text,
detects query type (decision vs advisory), normalises budget currency.

KEY FIXES:
1. Market is ALWAYS extracted from query text — the UI market field is a hint only
2. Advisory queries ("which field?", "give me ideas") → advisory pipeline, not GO/NO_GO
3. Budget in non-USD currencies (rupees, AED, SAR) → convert to USD
4. Product must be detected accurately — GPU/EV/semiconductor ≠ lending
"""

import json
import re
from datetime import datetime, timezone
from langchain_core.messages import SystemMessage, HumanMessage
from config.llm_config import get_fast_llm
from streaming.streamer import stream_event

# ── Currency conversion (approx rates to USD) ────────────────────────────────
_CURRENCY_HINTS = {
    "rupee": 0.012, "rupees": 0.012, "rupe": 0.012, "rupes": 0.012,
    "inr": 0.012, "rs": 0.012, "₹": 0.012,
    "aed": 0.272, "dirham": 0.272,
    "sar": 0.267, "riyal": 0.267,
    "gbp": 1.27, "pound": 1.27,
    "eur": 1.08, "euro": 1.08,
    "sgd": 0.74,
    "ngn": 0.00065, "naira": 0.00065,
    "kes": 0.0077, "shilling": 0.0077,
    "zar": 0.055, "rand": 0.055,
}

def _normalise_budget(query: str, budget_usd: float) -> tuple[float, str]:
    """Detect currency in query text and convert to USD."""
    q = query.lower()
    for hint, rate in _CURRENCY_HINTS.items():
        if hint in q:
            converted = round(budget_usd * rate, 0)
            return converted, f"{hint.upper()} → USD at {rate}"
    return budget_usd, "USD"

# ── Advisory query detection ──────────────────────────────────────────────────
_ADVISORY_PATTERNS = [
    r"which field", r"what field", r"which sector", r"what sector",
    r"where (should|can) i (invest|open|start|expand|launch)",
    r"give me (an idea|ideas|suggestion|suggestions|recommendation)",
    r"what (should|can) i (do|invest|start|open)",
    r"suggest (a|some|me)", r"recommend (a|some|me)",
    r"best (field|sector|market|industry|option)",
    r"good (field|sector|market|industry|option) (for|to)",
    r"what (business|startup|venture) (should|can)",
    r"ideas? for",
]

def _is_advisory(query: str) -> bool:
    q = query.lower()
    return any(re.search(p, q) for p in _ADVISORY_PATTERNS)

# ── Product taxonomy ─────────────────────────────────────────────────────────
_SYSTEM = """
You are an AI supervisor for a business decision system.
Extract structured information from the user query.

IMPORTANT RULES:
1. product_detected must be the EXACT product/service — not a category.
   Bad:  "lending"
   Good: "SME working capital lending"
   Bad:  "tech"
   Good: "GPU manufacturing" or "AI services platform" or "electric vehicle manufacturing"

2. market_detected must come from the QUERY TEXT first, then the provided market field.
   If the query says "India" and the market field says "UAE", use "India".
   If no market is in the query, use the provided market field.

3. query_type:
   - "decision"  → user wants GO/NO_GO on a specific opportunity
   - "advisory"  → user wants ideas, recommendations, or "which field" type guidance
   - "analysis"  → user wants market/financial analysis without a specific decision

4. product_class:
   - "lending"      → SME loans, retail lending, invoice financing, working capital
   - "ai_services"  → AI SaaS, AI APIs, AI products for customers
   - "manufacturing"→ hardware, semiconductors, EVs, physical goods
   - "edtech"       → education technology
   - "payments"     → payment processing, wallets, transfers
   - "other"        → anything else

Return ONLY this JSON:
{
  "product_detected":   "<exact product from query — not generic>",
  "product_class":      "lending|ai_services|manufacturing|edtech|payments|other",
  "market_detected":    "<country/region from QUERY TEXT — override UI field if different>",
  "query_type":         "decision|advisory|analysis",
  "budget_in_query":    <true|false — is a budget amount mentioned in the text?>,
  "currency_hint":      "<currency word found in query, e.g. 'rupees', 'AED', or 'USD'>",
  "is_ra_groups_query": <true|false — is this about RA Groups specifically?>,
  "advisory_topic":     "<if advisory: what the user wants ideas about, else null>",
  "notes":              "<any important observations>"
}
"""

async def supervisor_node(state: dict) -> dict:
    rid       = state["request_id"]
    raw_query = state["user_query"]
    ui_market = state.get("market", "")
    raw_budget = float(state.get("budget", 1_000_000))

    await stream_event(rid, "agent_start", "supervisor", "Analysing query")
    print(f"\n[supervisor] START  query={raw_query[:80]}")

    # ── Fast-path: detect advisory queries without LLM ───────────────────────
    if _is_advisory(raw_query):
        print(f"[supervisor] ADVISORY query detected (pattern match)")
        await stream_event(rid, "agent_complete", "supervisor", {
            "query_type": "advisory", "market": ui_market})
        return {
            "supervisor_plan":   {"query_type": "advisory", "advisory_topic": raw_query,
                                  "market_detected": ui_market},
            "routing_decision":  "advisory",
            "market":            ui_market,
            "product_type":      "advisory",
            "execution_log": [{"agent": "supervisor", "action": "advisory_detected",
                               "timestamp": datetime.now(timezone.utc).isoformat()}],
        }

    # ── LLM extraction ───────────────────────────────────────────────────────
    llm  = get_fast_llm()
    resp = await llm.ainvoke([
        SystemMessage(content=_SYSTEM),
        HumanMessage(content=(
            f"Query: {raw_query}\n"
            f"UI market field (hint only): {ui_market}\n"
            f"UI budget field: {raw_budget:,.0f}\n"
            f"UI timeline: {state.get('timeline_months', 12)} months"
        )),
    ])

    plan = {}
    try:
        cleaned = resp.content.strip().replace("```json","").replace("```","").strip()
        plan    = json.loads(cleaned)
    except Exception:
        plan = {
            "product_detected": raw_query[:60],
            "product_class":    "other",
            "market_detected":  ui_market,
            "query_type":       "decision",
        }

    # ── Override: market from query text beats UI field ──────────────────────
    extracted_market = plan.get("market_detected", "").strip()
    resolved_market  = extracted_market if extracted_market else ui_market
    if not resolved_market:
        resolved_market = ui_market or "unknown"

    # ── Normalise budget currency ─────────────────────────────────────────────
    budget_usd, currency_note = _normalise_budget(raw_query, raw_budget)
    if currency_note != "USD":
        print(f"[supervisor] Budget converted: {raw_budget:,.0f} {currency_note} → ${budget_usd:,.0f}")

    # ── Re-check advisory after LLM ─────────────────────────────────────────
    if plan.get("query_type") == "advisory":
        await stream_event(rid, "agent_complete", "supervisor", {
            "query_type": "advisory", "market": resolved_market})
        return {
            "supervisor_plan":   plan,
            "routing_decision":  "advisory",
            "market":            resolved_market,
            "budget":            budget_usd,
            "product_type":      "advisory",
            "execution_log": [{"agent": "supervisor", "action": "advisory_llm",
                               "timestamp": datetime.now(timezone.utc).isoformat()}],
        }

    print(f"[supervisor] product='{plan.get('product_detected')}'  "
          f"class='{plan.get('product_class')}'  market='{resolved_market}'  "
          f"budget_usd=${budget_usd:,.0f}  type={plan.get('query_type')}")

    await stream_event(rid, "agent_complete", "supervisor", {
        "product":      plan.get("product_detected"),
        "product_class": plan.get("product_class"),
        "market":       resolved_market,
        "type":         plan.get("query_type"),
        "budget_usd":   budget_usd,
    })

    return {
        "supervisor_plan":   plan,
        "routing_decision":  "parallel_research",
        "market":            resolved_market,          # ← FIXED: override state market
        "budget":            budget_usd,               # ← FIXED: currency-normalised
        "product_type":      plan.get("product_class", "other"),
        "_detected_product": plan.get("product_detected", raw_query[:60]),
        "_currency_note":    currency_note,
        "execution_log": [{
            "agent":        "supervisor",
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "action":       "query_analysed",
            "plan":         plan,
            "resolved_market": resolved_market,
            "budget_usd":   budget_usd,
            "currency_note": currency_note,
        }],
    }
