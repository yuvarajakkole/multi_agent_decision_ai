# app/nodes/market_research.py
# Market Research Agent using free yfinance data as a proxy signal.

from typing import Dict
import yfinance as yf
from langchain_core.runnables import RunnableConfig
from ..llm import get_llm
from ..models import DecisionState


def _fetch_index_snapshot(symbol: str = "^GSPC") -> Dict:
    """
    Fetches last 1 month performance of a market index using yfinance.
    Free, no key needed (Yahoo Finance public data). [web:52][web:75][web:78]
    """
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="1mo")
        if hist.empty:
            return {}
        first = hist.iloc[0]
        last = hist.iloc[-1]
        change_pct = (last["Close"] - first["Close"]) / first["Close"] * 100
        return {
            "symbol": symbol,
            "start_close": float(first["Close"]),
            "end_close": float(last["Close"]),
            "one_month_change_percent": round(float(change_pct), 2),
        }
    except Exception:
        return {}


def market_research_node(state: DecisionState, config: RunnableConfig) -> DecisionState:
    """
    Market Research Agent for RA Groups:
    - Uses yfinance as a macro/sector indicator.
    - LLM converts this + general knowledge into structured market insights.
    """
    llm = get_llm()

    business_query = state.get("business_query", "")
    market = state.get("market", "")

    # You can map specific indices per market; here is a generic one.
    index_snapshot = _fetch_index_snapshot("^GSPC")

    prompt = f"""
You are the Market Research Agent for RA Groups,
a diversified financial services and fintech company.

Business question: {business_query}
Target market: {market}

Here is some real market index data (used as a macro/sector sentiment proxy):
{index_snapshot}

Using this, plus your knowledge of financial services and fintech markets:

1. Estimate:
   - market_size_estimate (short text)
   - expected_growth_outlook (short text)
   - competitive_intensity (\"Low\" / \"Medium\" / \"High\" with 1-2 sentence explanation)

2. Provide bullet lists:
   - key_competitor_types (e.g. local banks, neobanks, BNPL players)
   - customer_segments (3-6 segments RA Groups could target)
   - regulatory_considerations (3-6 bullets)
   - technology_trends (3-6 bullets, especially AI / lending / risk)

3. Give an overall:
   - market_attractiveness (\"Low\" / \"Medium\" / \"High\" with 2-3 sentence reason)

Return a JSON-like dictionary as plain text with keys:
market_size_estimate, expected_growth_outlook, competitive_intensity,
key_competitor_types, customer_segments, regulatory_considerations,
technology_trends, market_attractiveness, summary_paragraph.


Also add a field:
- idea_fit_score (\"Low\" / \"Medium\" / \"High\") based on whether this business_query
  matches RA Groups' core_segments and product_portfolio.
If the query is in a completely different industry (cars, food factory, manufacturing),
idea_fit_score should be "Low" and strategic_fit_comment should clearly say this is outside
RA Groups' core capabilities.

    """

    answer = llm.invoke(prompt)

    result: Dict = {
        "raw_text": answer.content,
        "index_snapshot": index_snapshot,
    }

    return {"market_insights": result}
