# app/nodes/financial_risk.py
# Financial Risk Agent using yfinance data + LLM reasoning.

from typing import Dict
import yfinance as yf
from langchain_core.runnables import RunnableConfig
from ..llm import get_llm
from ..models import DecisionState


def _fetch_sector_proxy(symbol: str = "XLF") -> Dict:
    """
    Fetch 6 months performance of a financial sector ETF, e.g. XLF (US financials).
    This is a free proxy for sector sentiment. [web:52][web:75][web:78]
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="6mo")
        if hist.empty:
            return {}
        first = hist.iloc[0]
        last = hist.iloc[-1]
        change_pct = (last["Close"] - first["Close"]) / first["Close"] * 100
        return {
            "symbol": symbol,
            "start_price": float(first["Close"]),
            "end_price": float(last["Close"]),
            "six_month_change_percent": round(float(change_pct), 2),
        }
    except Exception:
        return {}


def financial_risk_node(state: DecisionState, config: RunnableConfig) -> DecisionState:
    """
    Financial Risk Agent for RA Groups:
    - Uses sector ETF performance from yfinance as an external financial signal.
    - Combines with RA Groups' budget to estimate ROI, payback, risk.
    """
    llm = get_llm()

    business_query = state.get("business_query", "")
    market = state.get("market", "")
    budget = state.get("budget", 0.0)

    sector_proxy = _fetch_sector_proxy("XLF")

    prompt = f"""

...
Your output must be realistic for RA Groups (fintech/lending company).
If the business_query is clearly outside RA Groups' core competence
(e.g. car showroom, manufacturing, unrelated industry), treat
overall_financial_attractiveness as "Weak" and financial_risk_level as "High",
unless there is a very strong reason not to.

Return:
- overall_financial_attractiveness: "Weak" / "Moderate" / "Strong"
- financial_risk_level: "Low" / "Medium" / "High"
...

    """

    answer = llm.invoke(prompt)

    result: Dict = {
        "raw_text": answer.content,
        "sector_proxy_data": sector_proxy,
    }

    return {"financial_analysis": result}
