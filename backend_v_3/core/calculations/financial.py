"""
core/calculations/financial.py
All critical metrics computed with real financial maths.
LLMs NEVER generate ROI, IRR, or payback period.

IMPORTANT — Fintech lending IRR model:
In a revolving lending book, the capital is not consumed — it generates recurring income.
Standard "project IRR" is misleading here. Instead we compute:
  - ROI:    (total income over period) / investment
  - IRR:    Return on Equity (ROE) = NIM / equity_ratio
            where NIM = net_yield - (cost_of_funds × leverage_ratio)
  - Payback: investment / monthly_net_income
"""

from typing import List


# ─── ROI ──────────────────────────────────────────────────────────────────────

def calculate_roi(revenue: float, cost: float) -> float:
    """
    ROI = (Revenue - Cost) / Cost * 100
    Returns percentage. Returns 0.0 if cost <= 0.
    """
    if cost <= 0:
        return 0.0
    return round(((revenue - cost) / cost) * 100, 2)


# ─── IRR (Fintech Lending Book Model) ────────────────────────────────────────

def calculate_irr_lending_book(
    net_yield_pct:      float,
    cost_of_funds_pct:  float = 4.0,
    leverage_ratio:     float = 0.60,
) -> float:
    """
    Compute IRR as Return on Equity (ROE) for a revolving fintech lending book.

    In fintech lending the deployed capital revolves — it is not consumed.
    The appropriate IRR for equity deployed is:
        NIM = net_yield - (cost_of_funds × leverage_ratio)
        ROE = NIM / (1 - leverage_ratio)

    Args:
        net_yield_pct    : net yield % after operating costs + NPL (e.g. 7.19)
        cost_of_funds_pct: RA Groups' own borrowing rate (default 4.0%)
        leverage_ratio   : fraction of loan book funded by debt (default 60%)

    Returns: IRR % as float, e.g. 11.98
    """
    if net_yield_pct <= 0:
        return 0.0
    equity_ratio = max(1.0 - leverage_ratio, 0.01)
    nim          = net_yield_pct - cost_of_funds_pct * leverage_ratio
    roe          = nim / equity_ratio
    return round(max(roe, -100.0), 2)


# Keep generic IRR for non-lending use cases
def calculate_irr(initial_investment: float, annual_cash_flows: List[float]) -> float:
    """
    General project IRR via bisection method.
    Use calculate_irr_lending_book() for revolving fintech lending books.
    Returns IRR as percentage.
    """
    if not annual_cash_flows or initial_investment <= 0:
        return 0.0
    if sum(annual_cash_flows) <= 0:
        return -100.0

    def npv(r: float) -> float:
        return -initial_investment + sum(
            cf / ((1.0 + r) ** i) for i, cf in enumerate(annual_cash_flows, 1)
        )

    # If project never breaks even at 0% discount, return simple rate
    if npv(0.0) <= 0:
        years  = len(annual_cash_flows)
        simple = (sum(annual_cash_flows) / initial_investment) / years - 1
        return round(simple * 100, 2)

    # Bisection
    lo, hi = -0.99, 10.0
    for _ in range(300):
        mid = (lo + hi) / 2
        if npv(mid) > 0:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1e-8:
            break
    return round(((lo + hi) / 2) * 100, 2)


# ─── Payback ──────────────────────────────────────────────────────────────────

def calculate_payback_months(investment: float, monthly_cash_flow: float) -> int:
    """
    Payback period in months = Investment / Monthly net cash flow.
    Returns 999 if cash flow is zero or negative.
    """
    if monthly_cash_flow <= 0:
        return 999
    return int(round(investment / monthly_cash_flow))


# ─── Product yield ────────────────────────────────────────────────────────────

_SPREADS = {
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

def calculate_product_yield(base_rate: float, product_type: str) -> float:
    """
    Gross product yield = base lending rate + benchmark spread.
    Longest-match wins to avoid partial matches (e.g. 'sme' vs 'sme working capital').
    """
    text   = product_type.lower()
    spread = next(
        (v for k, v in sorted(_SPREADS.items(), key=lambda x: -len(x[0])) if k in text),
        5.0
    )
    return round(base_rate + spread, 2)


def calculate_net_yield(
    gross_pct:  float,
    cost_ratio: float = 0.35,
    npl_ratio:  float = 0.030,
) -> float:
    """
    Net yield after operating costs and NPL provision.
    net_yield = gross_yield × (1 − cost_ratio) × (1 − npl_ratio)
    Returns percentage.
    """
    return round(gross_pct * (1.0 - cost_ratio) * (1.0 - npl_ratio), 2)


# ─── Attractiveness scoring ───────────────────────────────────────────────────

def score_financial_attractiveness(
    roi:    float,
    irr:    float,
    payback: int,
    risk:   str = "Medium",
) -> dict:
    """
    Deterministic 0-100 score.  RA Groups thresholds: ROI >= 25%, IRR >= 18%.
    """
    s = 0.0

    # ROI  (0–40 pts)
    if roi >= 40:    s += 40
    elif roi >= 25:  s += 30 + (roi - 25)
    elif roi >= 10:  s += 10 + (roi - 10) * 1.33
    elif roi >= 0:   s += roi * 0.5

    # IRR  (0–30 pts)
    if irr >= 25:    s += 30
    elif irr >= 18:  s += 20 + (irr - 18) * 1.43
    elif irr >= 8:   s += 5  + (irr - 8) * 1.5
    elif irr >= 0:   s += irr * 0.5

    # Payback  (0–20 pts)
    if payback <= 18:    s += 20
    elif payback <= 24:  s += 14
    elif payback <= 36:  s += 7
    elif payback >= 999: s += 0

    # Risk penalty  (−10 to 0)
    s += {"Low": 0, "Medium": -5, "High": -10}.get(risk, -5)
    s  = max(0.0, min(100.0, s))

    label = "Strong" if s >= 75 else "High" if s >= 55 else "Medium" if s >= 35 else "Low"
    return {
        "score":               round(s, 1),
        "label":               label,
        "meets_roi_threshold": roi >= 25,
        "meets_irr_threshold": irr >= 18,
        "roi_vs_threshold":    round(roi - 25, 1),
        "irr_vs_threshold":    round(irr - 18, 1),
    }
