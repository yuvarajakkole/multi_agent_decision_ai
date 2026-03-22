"""
core/calculations/financial.py  — Deterministic maths only. LLMs never compute these.
"""
from typing import List

_LENDING_KW = ["lending","loan","credit","sme lending","retail lending","invoice financing",
    "invoice","microfinance","working capital","embedded finance","mortgage",
    "debt","npl","nbfc","underwriting","lend","fintech lending"]
_NON_LENDING_KW = ["saas","software","edtech","education","ai agent","ai product","platform",
    "marketplace","app","insurance","wealthtech","payments","school","students",
    "teacher","learning","ecommerce","e-commerce","consumer product"]

def classify_product(text: str) -> str:
    t = text.lower()
    if any(k in t for k in _LENDING_KW):    return "lending"
    if any(k in t for k in _NON_LENDING_KW): return "non_lending"
    return "lending"

_LENDING_SPREADS = {"sme working capital":6.5,"sme lending":6.0,"sme":6.0,
    "working capital":6.5,"invoice financing":3.0,"invoice":3.0,
    "retail lending":8.0,"retail":8.0,"personal loan":9.0,"personal":9.0,
    "microfinance":10.0,"embedded finance":5.0}
_NON_LENDING_YIELDS = {"ai agent":40.0,"ai product":40.0,"edtech":30.0,"education":30.0,
    "saas":35.0,"software":35.0,"platform":28.0,"marketplace":25.0,
    "app":28.0,"payments":18.0,"insurance":20.0,"wealthtech":22.0}

def calculate_product_yield(base_rate: float, product_type: str) -> float:
    t = product_type.lower()
    if classify_product(t) == "non_lending":
        return round(next((v for k,v in sorted(_NON_LENDING_YIELDS.items(),key=lambda x:-len(x[0])) if k in t), 30.0), 2)
    spread = next((v for k,v in sorted(_LENDING_SPREADS.items(),key=lambda x:-len(x[0])) if k in t), 5.0)
    return round(base_rate + spread, 2)

def calculate_net_yield(gross: float, product_type: str = "") -> float:
    if classify_product(product_type) == "non_lending":
        return round(gross * 0.50, 2)
    return round(gross * 0.65 * 0.97, 2)

def calculate_roi(revenue: float, cost: float) -> float:
    if cost <= 0: return 0.0
    return round(((revenue - cost) / cost) * 100, 2)

def calculate_irr(net_yield: float, product_type: str, cost_of_funds: float = 4.0) -> float:
    if classify_product(product_type) == "non_lending":
        return round(net_yield, 2)
    nim = net_yield - cost_of_funds * 0.60
    return round(max(nim / 0.40, -100.0), 2)

def calculate_payback_months(investment: float, monthly_cash: float) -> int:
    if monthly_cash <= 0: return 999
    return int(round(investment / monthly_cash))

def score_financial_attractiveness(roi, irr, payback, risk="Medium", timeline_months=12) -> dict:
    s = 0.0; yrs = max(timeline_months/12, 1.0); aroi = roi/yrs
    if aroi>=35:s+=35
    elif aroi>=25:s+=25+(aroi-25)
    elif aroi>=15:s+=10+(aroi-15)*1.5
    elif aroi>=0:s+=aroi*0.5
    if irr>=25:s+=35
    elif irr>=18:s+=25+(irr-18)*1.43
    elif irr>=10:s+=8+(irr-10)*2.1
    elif irr>=0:s+=irr*0.6
    if payback<=24:s+=20
    elif payback<=48:s+=15
    elif payback<=84:s+=10
    elif payback<=180:s+=5
    elif payback<=300:s+=2
    s+={"Low":0,"Medium":-5,"High":-15,"Very High":-25}.get(risk,-10)
    s=max(0.0,min(100.0,s))
    label="Strong" if s>=70 else "High" if s>=52 else "Medium" if s>=35 else "Low"
    return {"score":round(s,1),"label":label,"meets_roi_threshold":aroi>=25,
            "meets_irr_threshold":irr>=18,"annualised_roi":round(aroi,2),
            "roi_gap":round(aroi-25,1),"irr_gap":round(irr-18,1)}
