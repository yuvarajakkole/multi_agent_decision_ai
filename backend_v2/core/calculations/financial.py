"""
core/calculations/financial.py
All critical metrics computed with real financial maths.
LLMs NEVER generate ROI, IRR, or payback period.
"""
from typing import List


# ─── ROI ──────────────────────────────────────────────────────────────────────

def calculate_roi(revenue: float, cost: float) -> float:
    """ROI = (Revenue - Cost) / Cost × 100.  Revenue = principal + net income."""
    if cost <= 0:
        return 0.0
    return round(((revenue - cost) / cost) * 100, 2)


# ─── IRR — Lending Book ROE Model ─────────────────────────────────────────────

def calculate_irr_lending_book(
    net_yield_pct:     float,
    cost_of_funds_pct: float = 4.0,
    leverage_ratio:    float = 0.60,
) -> float:
    """
    IRR for a revolving fintech lending book.
    NIM = net_yield - (cost_of_funds × leverage_ratio)
    IRR = NIM / (1 - leverage_ratio)
    """
    if net_yield_pct <= 0:
        return 0.0
    equity_ratio = max(1.0 - leverage_ratio, 0.01)
    nim          = net_yield_pct - cost_of_funds_pct * leverage_ratio
    return round(max(nim / equity_ratio, -100.0), 2)


# ─── Payback ──────────────────────────────────────────────────────────────────

def calculate_payback_months(investment: float, monthly_cash_flow: float) -> int:
    """Payback in months.  Returns 999 if cash flow ≤ 0."""
    if monthly_cash_flow <= 0:
        return 999
    return int(round(investment / monthly_cash_flow))


# ─── Product classification ───────────────────────────────────────────────────

_LENDING_KEYWORDS = [
    "lending", "loan", "credit", "sme lending", "retail lending",
    "invoice financing", "invoice", "microfinance", "working capital",
    "embedded finance", "mortgage", "debt", "npl", "nbfc", "underwriting", "lend",
]

_NON_LENDING_SIGNALS = [
    "saas", "software", "edtech", "education", "ai agent", "ai product",
    "platform", "marketplace", "app", "insurance", "wealthtech",
    "payments", "school", "students", "teacher", "learning",
]


def classify_product(product_type: str) -> str:
    """
    Returns 'lending' or 'non_lending'.
    Lending keywords always win — checked first.
    Defaults to 'lending' (RA Groups' core business).
    """
    text = product_type.lower()
    if any(kw in text for kw in _LENDING_KEYWORDS):
        return "lending"
    if any(kw in text for kw in _NON_LENDING_SIGNALS):
        return "non_lending"
    return "lending"


# ─── Product yield ────────────────────────────────────────────────────────────

_LENDING_SPREADS = {
    "sme working capital": 6.5,
    "sme lending":         6.0,
    "sme":                 6.0,
    "working capital":     6.5,
    "invoice financing":   3.0,
    "invoice":             3.0,
    "retail lending":      8.0,
    "retail":              8.0,
    "personal loan":       9.0,
    "personal":            9.0,
    "microfinance":       10.0,
    "embedded finance":    5.0,
}

_NON_LENDING_YIELDS = {
    "ai agent":    40.0,
    "ai product":  40.0,
    "edtech":      30.0,
    "education":   30.0,
    "saas":        35.0,
    "software":    35.0,
    "platform":    30.0,
    "marketplace": 25.0,
    "app":         28.0,
    "payments":    18.0,
    "insurance":   20.0,
    "wealthtech":  22.0,
}


def calculate_product_yield(base_rate: float, product_type: str) -> float:
    """
    Gross yield estimate.
    Lending products: base_rate + benchmark spread.
    Non-lending products: gross margin proxy (base_rate ignored).
    Longest-match wins within each category.
    """
    text  = product_type.lower()
    ptype = classify_product(text)

    if ptype == "non_lending":
        return round(next(
            (v for k, v in sorted(_NON_LENDING_YIELDS.items(), key=lambda x: -len(x[0]))
             if k in text),
            30.0,
        ), 2)
    else:
        spread = next(
            (v for k, v in sorted(_LENDING_SPREADS.items(), key=lambda x: -len(x[0]))
             if k in text),
            5.0,
        )
        return round(base_rate + spread, 2)


def calculate_net_yield(
    gross_pct:    float,
    cost_ratio:   float = 0.35,
    npl_ratio:    float = 0.030,
    product_type: str   = "",
) -> float:
    """Net yield after operating costs and NPL provision."""
    if classify_product(product_type) == "non_lending":
        cost_ratio = 0.50  # higher opex for tech
        npl_ratio  = 0.0   # no loan losses
    return round(gross_pct * (1.0 - cost_ratio) * (1.0 - npl_ratio), 2)


# ─── Attractiveness scoring ───────────────────────────────────────────────────

def score_financial_attractiveness(
    roi:             float,
    irr:             float,
    payback:         int,
    risk:            str = "Medium",
    timeline_months: int = 12,
) -> dict:
    """
    Deterministic 0-100 score.  RA Groups: IRR >= 18%, annualised ROI >= 25%.
    Short timelines naturally produce lower absolute ROI — we annualise for fairness.
    """
    s     = 0.0
    years = max(timeline_months / 12, 1.0)
    ann_roi = roi / years          # annualised ROI for fair comparison

    # ROI  (0–40)
    if ann_roi >= 40:    s += 40
    elif ann_roi >= 25:  s += 30 + (ann_roi - 25)
    elif ann_roi >= 10:  s += 10 + (ann_roi - 10) * 1.33
    elif ann_roi >= 0:   s += ann_roi * 0.5

    # IRR  (0–30)
    if irr >= 25:    s += 30
    elif irr >= 18:  s += 20 + (irr - 18) * 1.43
    elif irr >= 10:  s += 5  + (irr - 10) * 1.25
    elif irr >= 0:   s += irr * 0.4

    # Payback  (0–20) — context-aware for lending books
    if payback <= 18:     s += 20
    elif payback <= 36:   s += 16
    elif payback <= 60:   s += 12
    elif payback <= 120:  s += 8
    elif payback <= 240:  s += 4

    # Risk penalty  (−10 to 0)
    s += {"Low": 0, "Medium": -5, "High": -10}.get(risk, -5)
    s  = max(0.0, min(100.0, s))

    label = "Strong" if s >= 75 else "High" if s >= 55 else "Medium" if s >= 35 else "Low"
    return {
        "score":               round(s, 1),
        "label":               label,
        "meets_roi_threshold": ann_roi >= 25,
        "meets_irr_threshold": irr >= 18,
        "annualised_roi":      round(ann_roi, 2),
        "roi_vs_threshold":    round(ann_roi - 25, 1),
        "irr_vs_threshold":    round(irr - 18, 1),
    }
