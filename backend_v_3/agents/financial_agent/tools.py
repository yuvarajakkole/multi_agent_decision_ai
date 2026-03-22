"""
Financial Agent Tools — real APIs + deterministic calculations.
LLM NEVER computes ROI, IRR or payback — those come from core/calculations/financial.py.
"""
import requests
import yfinance as yf
from langchain_core.tools import tool
from core.reliability.fallback import get_fallback_macro, get_fallback_fx, _CODES

# ─── Verified Yahoo Finance symbols (tested March 2025) ──────────────────────
# UAE/GCC indices are not on Yahoo; we use ETF proxies instead.
_INDEX_MAP = {
    "AE": "EWQ",    # MSCI Qatar ETF — best GCC proxy available on Yahoo
    "SA": "KSA",    # iShares MSCI Saudi Arabia ETF
    "IN": "^NSEI",  # Nifty 50 — verified
    "ID": "^JKSE",  # Jakarta — verified
    "SG": "EWS",    # iShares MSCI Singapore ETF
    "MY": "EWM",    # iShares MSCI Malaysia ETF
    "GB": "^FTSE",  # FTSE 100 — verified
    "US": "^GSPC",  # S&P 500 — verified
    "DE": "^GDAXI", # DAX — verified
    "EG": "EGPT",   # VanEck Egypt ETF
    "QA": "EWQ",    # Qatar proxy
    "KW": "GULF",   # Gulf States ETF
}

# Fintech ETF proxies by region
_ETF_MAP = {
    "AE": "FINX",  # Global X FinTech ETF
    "SA": "FINX",
    "IN": "INDA",  # iShares MSCI India
    "ID": "EIDO",  # iShares MSCI Indonesia
    "SG": "EWS",
    "MY": "EWM",
    "GB": "FINX",
    "US": "FINX",
    "DE": "FINX",
}


@tool
def get_real_macro_indicators(market: str) -> dict:
    """Fetch lending rate, inflation, GDP growth from World Bank Open API (free, no key)."""
    code = _CODES.get(market.lower().strip(), market[:2].upper())
    indicators = {
        "FR.INR.LEND":       "lending_rate_pct",
        "FP.CPI.TOTL.ZG":    "inflation_pct",
        "NY.GDP.MKTP.KD.ZG": "gdp_growth_pct",
        "BN.CAB.XOKA.GD.ZS": "current_account_gdp_pct",
    }
    out  = {"source": "World Bank API", "country_code": code}
    base = "https://api.worldbank.org/v2/country"

    for ind, key in indicators.items():
        try:
            r   = requests.get(
                f"{base}/{code}/indicator/{ind}?format=json&mrv=3&per_page=3",
                timeout=10
            )
            d   = r.json()
            val = next(
                (e["value"] for e in (d[1] or []) if e.get("value") is not None), None
            )
            out[key] = round(float(val), 2) if val is not None else "N/A"
        except Exception:
            out[key] = "N/A"

    # Fill missing lending rate with fallback
    if out.get("lending_rate_pct") == "N/A":
        fb = get_fallback_macro(market)
        out["lending_rate_pct"] = fb["lending_rate"]
        out["source"]           = "World Bank + fallback_static"

    return out


@tool
def get_currency_exchange_rate(base_currency: str, target_currency: str = "USD") -> dict:
    """Live FX rate from open.er-api.com (free, no key required)."""
    try:
        r = requests.get(
            f"https://open.er-api.com/v6/latest/{base_currency.upper()}",
            timeout=8
        )
        d = r.json()
        if d.get("result") == "success":
            rate = d["rates"].get(target_currency.upper())
            return {
                "source": "er-api.com",
                "base":   base_currency.upper(),
                "target": target_currency.upper(),
                "rate":   round(rate, 4) if rate else "N/A",
            }
    except Exception:
        pass
    return get_fallback_fx(base_currency)


@tool
def get_stock_market_index(market: str) -> dict:
    """
    Regional stock market / ETF performance via yfinance.
    Uses ETF proxies for markets where direct index symbols are unavailable on Yahoo Finance
    (e.g. UAE, Saudi Arabia, Kuwait — their native indices are not on Yahoo).
    """
    code   = _CODES.get(market.lower().strip(), market[:2].upper())
    symbol = _INDEX_MAP.get(code, "^GSPC")   # default to S&P500 as global benchmark

    try:
        ticker = yf.Ticker(symbol)
        hist   = ticker.history(period="1mo")
        if not hist.empty:
            start = float(hist.iloc[0]["Close"])
            end   = float(hist.iloc[-1]["Close"])
            chg   = round((end - start) / start * 100, 2)
            sentiment = "Positive" if chg > 2 else "Negative" if chg < -2 else "Neutral"
            return {
                "source":               "yfinance",
                "symbol":               symbol,
                "is_proxy":             not symbol.startswith("^"),
                "one_month_change_pct": chg,
                "sentiment":            sentiment,
                "note": "ETF proxy used — direct index unavailable on Yahoo Finance" if not symbol.startswith("^") else "",
            }
    except Exception as e:
        print(f"[stock_index] yfinance error for {symbol}: {e}")

    return {
        "source":               "fallback",
        "symbol":               symbol,
        "one_month_change_pct": "N/A",
        "sentiment":            "Neutral",
        "note":                 "Market data unavailable — using neutral sentiment",
    }


@tool
def get_fintech_etf_performance(market: str) -> dict:
    """
    Fintech ETF performance as a proxy for fintech sector sentiment in the target market.
    FINX (Global X FinTech ETF) used as global benchmark when regional ETF unavailable.
    """
    code   = _CODES.get(market.lower().strip(), market[:2].upper())
    symbol = _ETF_MAP.get(code, "FINX")

    try:
        ticker = yf.Ticker(symbol)
        hist   = ticker.history(period="3mo")
        if not hist.empty:
            start = float(hist.iloc[0]["Close"])
            end   = float(hist.iloc[-1]["Close"])
            chg   = round((end - start) / start * 100, 2)
            sentiment = "Bullish" if chg > 3 else "Bearish" if chg < -3 else "Neutral"
            return {
                "source":                 "yfinance",
                "symbol":                 symbol,
                "three_month_change_pct": chg,
                "fintech_sentiment":      sentiment,
            }
    except Exception as e:
        print(f"[fintech_etf] yfinance error for {symbol}: {e}")

    return {
        "source":                 "fallback",
        "symbol":                 symbol,
        "three_month_change_pct": "N/A",
        "fintech_sentiment":      "Neutral",
    }
