"""
core/calculations/financial.py

All deterministic financial maths.  LLMs never compute numbers.

FIXED:
- Expanded product taxonomy — GPU/semiconductor/EV/manufacturing classified correctly
- AI services ≠ lending
- Non-lending gross margins reflect actual business economics
- Confidence always computed from actual data quality (never hardcoded 100%)
"""

# ─── Product classification ───────────────────────────────────────────────────

# Must be checked BEFORE lending keywords to prevent "ai lending" → ai_services
_AI_SERVICES_KW = [
    "ai services", "ai service", "ai company", "ai startup", "ai platform",
    "ai saas", "ai api", "ai product", "ai solution", "ai tool",
    "artificial intelligence service", "machine learning service",
    "ml service", "ai for customer", "ai for business",
]
_MANUFACTURING_KW = [
    "gpu", "semiconductor", "chip", "chipset", "wafer", "fabrication",
    "electric vehicle", "ev manufacturing", "automobile", "automotive",
    "solar panel", "hardware manufacturing", "factory", "plant",
    "microchip", "integrated circuit", "pcb", "printed circuit",
    "battery manufacturing", "drone manufacturing",
]
_EDTECH_KW = [
    "edtech", "education technology", "e-learning", "elearning",
    "online learning", "learning management", "lms", "school platform",
    "tutoring platform", "course platform", "educational app",
]
_PAYMENTS_KW = [
    "payment gateway", "payment processing", "digital wallet",
    "money transfer", "remittance", "mobile money", "neobank",
    "payment app", "finpay", "paytech",
]
_SAAS_KW = [
    "saas", "software as a service", "cloud software", "crm software",
    "erp software", "hr software", "enterprise software", "b2b software",
    "vertical saas", "platform as a service",
]
_LENDING_KW = [
    "sme working capital", "sme lending", "working capital", "invoice financing",
    "retail lending", "personal loan", "microfinance", "embedded finance",
    "lending platform", "loan platform", "credit platform",
    "lending", "loan", "credit", "invoice", "nbfc", "underwriting", "lend",
    "fintech lending", "digital lending",
]


def classify_product(text: str) -> str:
    """
    Returns one of: lending | ai_services | manufacturing | edtech | payments | saas | non_lending
    'non_lending' is returned for anything that isn't lending.
    Checks manufacturing and AI services FIRST to prevent misclassification.
    """
    t = text.lower()

    # Manufacturing always wins — never lending
    for kw in _MANUFACTURING_KW:
        if kw in t:
            return "manufacturing"

    # AI services — check before lending
    for kw in _AI_SERVICES_KW:
        if kw in t:
            return "ai_services"

    # If it's just "ai" without "lending" context, treat as ai_services
    if ("ai" in t or "artificial intelligence" in t) and not any(lkw in t for lkw in _LENDING_KW):
        return "ai_services"

    # Edtech
    for kw in _EDTECH_KW:
        if kw in t:
            return "edtech"

    # Payments
    for kw in _PAYMENTS_KW:
        if kw in t:
            return "payments"

    # SaaS
    for kw in _SAAS_KW:
        if kw in t:
            return "saas"

    # Lending — checked last
    for kw in _LENDING_KW:
        if kw in t:
            return "lending"

    return "non_lending"   # unknown non-lending product


def is_non_lending(product_class: str) -> bool:
    return product_class != "lending"


# ─── Yield / margin tables ────────────────────────────────────────────────────

# Lending: spread over base lending rate
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

# Non-lending: gross margin % (revenue - COGS) / revenue
_NON_LENDING_GROSS_MARGINS = {
    # AI services
    "ai_services":    45.0,
    "ai services":    45.0,
    "ai company":     40.0,
    # Manufacturing (much lower margins)
    "manufacturing":  18.0,
    "gpu":            22.0,
    "semiconductor":  25.0,
    "electric vehicle": 8.0,
    "ev manufacturing": 8.0,
    # Edtech
    "edtech":         35.0,
    "education":      32.0,
    # Payments
    "payments":       30.0,
    # SaaS
    "saas":           70.0,
    "software":       60.0,
    # Fallback
    "platform":       40.0,
    "app":            35.0,
    "marketplace":    30.0,
}


def get_product_yield(base_lending_rate: float, query: str) -> float:
    """Gross yield/margin % for this product."""
    t     = query.lower()
    ptype = classify_product(t)

    if ptype == "lending":
        for kw, spread in sorted(_LENDING_SPREADS.items(), key=lambda x: -len(x[0])):
            if kw in t:
                return round(base_lending_rate + spread, 2)
        return round(base_lending_rate + 5.0, 2)

    # Non-lending: return gross margin
    for kw, margin in sorted(_NON_LENDING_GROSS_MARGINS.items(), key=lambda x: -len(x[0])):
        if kw in t or kw == ptype:
            return round(margin, 2)
    return 30.0   # default non-lending gross margin


def get_net_yield(gross: float, query: str) -> float:
    """
    Net yield after all costs.
    Lending:        65% efficiency ratio, 3% NPL
    Manufacturing:  very thin — 40% of gross (high capex, depreciation)
    AI services:    60% of gross (R&D, cloud, sales)
    SaaS:           75% of gross (low marginal cost)
    Edtech:         55% of gross
    Other non-lending: 50% of gross
    """
    ptype = classify_product(query)
    if ptype == "lending":
        return round(gross * 0.65 * (1 - 0.03), 2)
    if ptype == "manufacturing":
        return round(gross * 0.40, 2)
    if ptype == "saas":
        return round(gross * 0.75, 2)
    if ptype == "ai_services":
        return round(gross * 0.60, 2)
    if ptype == "edtech":
        return round(gross * 0.55, 2)
    return round(gross * 0.50, 2)   # default non-lending


# ─── Core financial metrics ────────────────────────────────────────────────────

def calc_roi(revenue: float, cost: float) -> float:
    if cost <= 0:
        return 0.0
    return round(((revenue - cost) / cost) * 100, 2)


def calc_irr(net_yield: float, query: str, cost_of_funds: float = 4.0) -> float:
    """
    Lending:        ROE model (NIM ÷ equity ratio)
    Manufacturing:  net_yield − WACC (high capex, low IRR for risky ventures)
    Other:          net_yield ≈ IRR directly
    """
    ptype = classify_product(query)
    if ptype == "lending":
        nim = net_yield - (cost_of_funds * 0.60)
        return round(max(nim / 0.40, -100.0), 2)
    if ptype == "manufacturing":
        wacc = 12.0   # high WACC for capital-intensive manufacturing
        return round(net_yield - wacc, 2)
    return round(net_yield, 2)


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
    Score 0–100.  Both strong (GO) and weak (NO_GO) results are scored honestly.
    Uses annualised ROI for fair short-timeline comparison.
    """
    score = 0.0
    years = max(timeline_months / 12, 1.0)
    annualised_roi = roi / years

    # ROI component (0–35)
    if annualised_roi >= 35:    score += 35
    elif annualised_roi >= 25:  score += 25 + (annualised_roi - 25)
    elif annualised_roi >= 15:  score += 10 + (annualised_roi - 15) * 1.5
    elif annualised_roi >= 0:   score += annualised_roi * 0.5
    else:                       score += max(annualised_roi * 0.3, -10)

    # IRR component (0–35)
    if irr >= 25:    score += 35
    elif irr >= 18:  score += 25 + (irr - 18) * 1.43
    elif irr >= 10:  score += 8  + (irr - 10) * 2.1
    elif irr >= 0:   score += irr * 0.6
    else:            score += max(irr * 0.5, -10)

    # Payback component (0–20)
    if payback <= 24:    score += 20
    elif payback <= 48:  score += 15
    elif payback <= 84:  score += 10
    elif payback <= 180: score += 5
    elif payback <= 300: score += 2

    # Risk penalty
    score += {"Low": 0, "Medium": -5, "High": -15, "Very High": -25}.get(risk, -10)

    score = max(-20.0, min(100.0, score))

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
        "meets_roi_target":  annualised_roi >= 25,
        "meets_irr_target":  irr >= 18,
        "roi_gap":           round(annualised_roi - 25, 1),
        "irr_gap":           round(irr - 18, 1),
    }
