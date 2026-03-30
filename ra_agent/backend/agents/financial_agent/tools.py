"""agents/financial_agent/tools.py"""

import requests
import yfinance as yf
from langchain_core.tools import tool
from core.reliability.market_data import iso_code, get_macro

_ETF_MAP = {
    "AE": "KSA",  "SA": "KSA",  "IN": "INDA", "ID": "EIDO",
    "SG": "EWS",  "MY": "EWM",  "EG": "EGPT", "KE": "AFK",
    "NG": "AFK",  "ZA": "EZA",  "GB": "EWU",  "US": "SPY",
    "DE": "EWG",  "BR": "EWZ",  "TR": "TUR",
}

_WB_BASE = "https://api.worldbank.org/v2/country/{code}/indicator/{ind}?format=json&mrv=3&per_page=3"


@tool
def get_macro_indicators(market: str) -> dict:
    """
    Fetch real macro indicators from World Bank: lending rate, inflation, GDP growth.
    Falls back to static benchmarks if API unavailable.
    """
    code = iso_code(market)
    indicators = {
        "FR.INR.LEND":        "lending_rate_pct",
        "FP.CPI.TOTL.ZG":     "inflation_pct",
        "NY.GDP.MKTP.KD.ZG":  "gdp_growth_pct",
    }
    out = {"source": "World Bank API", "country_code": code}
    any_live = False

    for ind, key in indicators.items():
        try:
            r   = requests.get(_WB_BASE.format(code=code, ind=ind), timeout=10)
            d   = r.json()
            val = next(
                (e["value"] for e in (d[1] or []) if e.get("value") is not None),
                None
            )
            out[key] = round(float(val), 2) if val is not None else None
            if val is not None:
                any_live = True
        except Exception:
            out[key] = None

    # Fill any missing values from static fallback
    fb = get_macro(market)
    for key, fb_key in [("lending_rate_pct", "lending_rate"),
                         ("gdp_growth_pct",   "gdp_growth"),
                         ("inflation_pct",    "inflation")]:
        if out.get(key) is None:
            out[key] = fb[fb_key]
            out[f"_{key}_source"] = "static_fallback"

    out["data_quality"] = "High" if any_live else "Low"
    return out


@tool
def get_fx_rate(currency: str) -> dict:
    """
    Fetch live USD exchange rate from open.er-api.com.
    Falls back to known rates if API unavailable.
    """
    _KNOWN = {
        "AED": 3.67, "SAR": 3.75, "INR": 83.5,  "IDR": 15800,
        "SGD": 1.34, "MYR": 4.72, "EGP": 48.0,  "QAR": 3.64,
        "KES": 129,  "NGN": 1550, "ZAR": 18.5,  "GBP": 0.79,
        "EUR": 0.92, "BRL": 4.97, "TRY": 32.5,
    }
    cur = currency.upper().strip()
    try:
        r = requests.get(f"https://open.er-api.com/v6/latest/{cur}", timeout=8)
        d = r.json()
        if d.get("result") == "success":
            usd_rate = d["rates"].get("USD", 0)
            return {
                "source":   "er-api.com",
                "currency": cur,
                "usd_rate": round(usd_rate, 4),
                "date":     d.get("time_last_update_utc", ""),
                "live":     True,
            }
    except Exception:
        pass
    known = _KNOWN.get(cur)
    return {
        "source":   "static_fallback",
        "currency": cur,
        "usd_rate": known,
        "live":     False,
    }


@tool
def get_sector_sentiment(market: str) -> dict:
    """
    Use an ETF as proxy for financial sector sentiment in this market.
    Returns 3-month performance and derived sentiment label.
    """
    code = iso_code(market)
    sym  = _ETF_MAP.get(code, "FINX")  # FINX = global fintech ETF as fallback
    try:
        hist = yf.Ticker(sym).history(period="3mo")
        if not hist.empty:
            start = float(hist.iloc[0]["Close"])
            end   = float(hist.iloc[-1]["Close"])
            chg   = round((end - start) / start * 100, 2)
            sentiment = "Bullish" if chg > 5 else "Bearish" if chg < -5 else "Neutral"
            return {
                "source":             "yfinance",
                "symbol":             sym,
                "is_proxy":           True,
                "three_month_chg_pct": chg,
                "sentiment":          sentiment,
                "live":               True,
            }
    except Exception as e:
        print(f"[sector_sentiment] yfinance error for {sym}: {e}")

    return {
        "source":             "fallback",
        "symbol":             sym,
        "three_month_chg_pct": None,
        "sentiment":          "Neutral",
        "live":               False,
    }
