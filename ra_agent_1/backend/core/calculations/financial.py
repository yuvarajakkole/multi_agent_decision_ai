"""
core/calculations/financial.py

All deterministic financial maths.  LLMs never compute numbers — they only
interpret results and provide qualitative analysis.

Product classification → yield table → net yield → ROI/IRR/payback → score
"""

# ─── Product classification ───────────────────────────────────────────────────

_LENDING_KW = [
    "sme working capital", "sme lending", "working capital", "invoice financing",
    "retail lending", "personal loan", "microfinance", "embedded finance",
    "lending", "loan", "credit", "invoice", "nbfc", "underwriting", "lend",
]
_NON_LENDING_KW = [
    "saas", "software", "edtech", "education", "ai agent", "ai product",
    "platform", "marketplace", "app", "insurance", "wealthtech", "payments",
    "school", "students", "teacher", "learning", "ecommerce",
]


def classify_product(text: str) -> str:
    """Returns 'lending' or 'non_lending'."""
    t = text.lower()
    # Lending keywords checked first — they always win
    for kw in _LENDING_KW:
        if kw in t:
            return "lending"
    for kw in _NON_LENDING_KW:
        if kw in t:
            return "non_lending"
    return "lending"  # RA Groups default business


# ─── Yield tables ─────────────────────────────────────────────────────────────

_LENDING_SPREADS = {
    "sme working capital": 6.5,
    "sme lending":         6.0,
    "working capital":     6.5,
    "invoice financing":   3.0,
    "invoice":             3.0,
    "retail lending":      8.0,
    "retail":              8.0,
    "personal loan":       9.0,
    "microfinance":       10.0,
    "embedded finance":    5.0,
    "sme":                 6.0,
}

_NON_LENDING_GROSS_MARGINS = {
    "ai agent":    42.0,
    "ai product":  42.0,
    "edtech":      30.0,
    "education":   30.0,
    "saas":        35.0,
    "software":    33.0,
    "platform":    28.0,
    "marketplace": 25.0,
    "app":         28.0,
    "payments":    20.0,
    "insurance":   22.0,
    "wealthtech":  25.0,
}


def get_product_yield(base_lending_rate: float, query: str) -> float:
    """Gross yield percentage for this product."""
    t = query.lower()
    if classify_product(t) == "non_lending":
        for kw, margin in sorted(_NON_LENDING_GROSS_MARGINS.items(), key=lambda x: -len(x[0])):
            if kw in t:
                return round(margin, 2)
        return 30.0
    # Lending: base rate + spread
    for kw, spread in sorted(_LENDING_SPREADS.items(), key=lambda x: -len(x[0])):
        if kw in t:
            return round(base_lending_rate + spread, 2)
    return round(base_lending_rate + 5.0, 2)


def get_net_yield(gross: float, query: str) -> float:
    """
    Net yield after operating costs and credit losses.
    Lending:     65% cost efficiency, 3% NPL haircut
    Non-lending: 50% opex ratio, 0 NPL
    """
    if classify_product(query) == "non_lending":
        return round(gross * 0.50, 2)
    return round(gross * 0.65 * (1 - 0.03), 2)


# ─── Core financial metrics ────────────────────────────────────────────────────

def calc_roi(revenue: float, cost: float) -> float:
    if cost <= 0:
        return 0.0
    return round(((revenue - cost) / cost) * 100, 2)


def calc_irr(net_yield: float, query: str, cost_of_funds: float = 4.0) -> float:
    """
    Lending: ROE model (NIM / equity ratio)
    Non-lending: net yield ≈ IRR directly
    """
    if classify_product(query) == "non_lending":
        return round(net_yield, 2)
    nim = net_yield - (cost_of_funds * 0.60)
    return round(max(nim / 0.40, -100.0), 2)


def calc_payback_months(investment: float, monthly_cash_flow: float) -> int:
    if monthly_cash_flow <= 0:
        return 999
    return int(round(investment / monthly_cash_flow))


# ─── Attractiveness scoring ────────────────────────────────────────────────────

def score_financials(
    roi: float,
    irr: float,
    payback: int,
    risk: str = "Medium",
    timeline_months: int = 12,
) -> dict:
    """
    Score 0–100.  Uses annualised ROI so short timelines aren't penalised.
    Both strong (GO) and weak (NO_GO) results are scored honestly.
    """
    score = 0.0
    years = max(timeline_months / 12, 1.0)
    annualised_roi = roi / years

    # ROI component (0–35)
    if annualised_roi >= 35:    score += 35
    elif annualised_roi >= 25:  score += 25 + (annualised_roi - 25)
    elif annualised_roi >= 15:  score += 10 + (annualised_roi - 15) * 1.5
    elif annualised_roi >= 0:   score += annualised_roi * 0.5
    else:                       score += max(annualised_roi * 0.3, -10)  # negative ROI hurts

    # IRR component (0–35)
    if irr >= 25:    score += 35
    elif irr >= 18:  score += 25 + (irr - 18) * 1.43
    elif irr >= 10:  score += 8  + (irr - 10) * 2.1
    elif irr >= 0:   score += irr * 0.6
    else:            score += max(irr * 0.5, -10)  # negative IRR hurts

    # Payback component (0–20)
    if payback <= 24:    score += 20
    elif payback <= 48:  score += 15
    elif payback <= 84:  score += 10
    elif payback <= 180: score += 5
    elif payback <= 300: score += 2

    # Risk penalty
    score += {
        "Low":       0,
        "Medium":   -5,
        "High":    -15,
        "Very High":-25,
    }.get(risk, -10)

    score = max(-20.0, min(100.0, score))  # allow slightly negative for very bad cases

    label = (
        "Strong"   if score >= 70 else
        "Good"     if score >= 55 else
        "Marginal" if score >= 35 else
        "Weak"     if score >= 10 else
        "Poor"
    )

    return {
        "score":             round(score, 1),
        "label":             label,
        "annualised_roi":    round(annualised_roi, 2),
        "meets_roi_target":  annualised_roi >= 25,   # RA Groups threshold
        "meets_irr_target":  irr >= 18,              # RA Groups threshold
        "roi_gap":           round(annualised_roi - 25, 1),
        "irr_gap":           round(irr - 18, 1),
    }
