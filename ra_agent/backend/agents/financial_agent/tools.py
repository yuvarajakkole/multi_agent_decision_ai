"""agents/financial_agent/tools.py

Updated to:
  1. Use get_macro() envelope API — source/confidence surfaced, not hidden
  2. iso_code() → resolve_iso() — no more market[:2] truncation
  3. Static fallback explicitly labelled in output (not silent)
  4. Sector sentiment reports source and confidence
"""

import requests
import yfinance as yf
from langchain_core.tools import tool
from core.reliability.market_data import resolve_iso, get_macro

_WB_BASE = "https://api.worldbank.org/v2/country/{code}/indicator/{ind}?format=json&mrv=3&per_page=3"

_ETF_MAP = {
    "AE": "KSA",  "SA": "KSA",  "IN": "INDA", "ID": "EIDO",
    "SG": "EWS",  "MY": "EWM",  "EG": "EGPT", "KE": "AFK",
    "NG": "AFK",  "ZA": "EZA",  "GB": "EWU",  "US": "SPY",
    "DE": "EWG",  "BR": "EWZ",  "TR": "TUR",
}


def _safe_iso(market: str) -> str:
    iso = resolve_iso(market)
    return iso if iso is not None else "UNKNOWN"


@tool
def get_macro_indicators(market: str) -> dict:
    """
    Fetch macroeconomic indicators: lending rate, inflation, GDP growth.
    Uses World Bank live API first; explicitly falls back to static benchmarks
    only if live fails. Source and confidence always reported.
    """
    env  = get_macro(market)
    data = env["data"]

    out = {
        "source":           env["source"],
        "confidence":       env["confidence"],
        "ignore":           env["ignore"],
        "warnings":         env["warnings"],
        "country_code":     data.get("country_code", "UNKNOWN"),
        "lending_rate_pct": data.get("lending_rate"),
        "inflation_pct":    data.get("inflation"),
        "gdp_growth_pct":   data.get("gdp_growth"),
        "gdp_per_capita_usd": data.get("gdp_per_capita_usd"),
        "unemployment_pct": data.get("unemployment_pct"),
        "fintech_maturity": data.get("fintech_maturity"),
        "macro_risk":       data.get("macro_risk"),
    }

    # Any None in critical fields → mark data_quality Low
    critical = ["lending_rate_pct", "inflation_pct", "gdp_growth_pct"]
    missing  = [k for k in critical if out.get(k) is None]
    out["data_quality"]       = "Low" if missing else "High"
    out["missing_critical"]   = missing

    if env["ignore"]:
        out["AGENT_WARNING"] = (
            f"Market '{market}' data confidence={env['confidence']:.2f} is below threshold. "
            f"Financial calculations using this data will be unreliable."
        )

    return out


@tool
def get_fx_rate(currency: str) -> dict:
    """
    Fetch live USD exchange rate. Falls back to known static rates if API fails.
    Static fallback is clearly labelled — never silent.
    """
    _KNOWN_RATES = {
        "AED": 0.272, "SAR": 0.267, "INR": 0.012, "IDR": 0.000063,
        "SGD": 0.74,  "MYR": 0.22,  "EGP": 0.021, "QAR": 0.274,
        "KES": 0.0077,"NGN": 0.00065,"ZAR": 0.055, "GBP": 1.27,
        "EUR": 1.08,  "BRL": 0.20,  "TRY": 0.031,
    }
    cur = currency.upper().strip()
    if not cur:
        return {"source": "no_currency", "confidence": 0.0, "usd_rate": None}

    try:
        r = requests.get(f"https://open.er-api.com/v6/latest/{cur}", timeout=8)
        r.raise_for_status()
        d = r.json()
        if d.get("result") == "success":
            rate = d["rates"].get("USD")
            if rate:
                return {
                    "source":     "live_api:er-api.com",
                    "confidence": 1.0,
                    "currency":   cur,
                    "usd_rate":   round(float(rate), 6),
                    "updated":    d.get("time_last_update_utc", ""),
                }
    except Exception as exc:
        pass

    known = _KNOWN_RATES.get(cur)
    return {
        "source":     "static_fallback",
        "confidence": 0.30,
        "currency":   cur,
        "usd_rate":   known,
        "warning":    f"Live FX API unavailable — using static rate for {cur} (may be outdated)",
    }


@tool
def get_sector_sentiment(market: str) -> dict:
    """
    ETF-based proxy for financial sector sentiment in this market.
    Reports exactly which ETF, change %, derived sentiment, and whether live.
    Returns Neutral with confidence=0.1 when data unavailable — never fabricates.
    """
    code = _safe_iso(market)
    sym  = _ETF_MAP.get(code, "FINX")

    try:
        hist = yf.Ticker(sym).history(period="3mo")
        if hist is not None and not hist.empty:
            start = float(hist.iloc[0]["Close"])
            end   = float(hist.iloc[-1]["Close"])
            chg   = round((end - start) / start * 100, 2)
            label = "Bullish" if chg > 5 else "Bearish" if chg < -5 else "Neutral"
            return {
                "source":              "live_api:yfinance",
                "confidence":          0.7,   # ETF proxy — indicative not definitive
                "symbol":              sym,
                "is_proxy":            True,
                "country_code":        code,
                "three_month_chg_pct": chg,
                "sentiment":           label,
                "note": f"{sym} ETF used as proxy for {market} financial sector",
            }
    except Exception as exc:
        pass

    return {
        "source":              "unavailable",
        "confidence":          0.1,
        "symbol":              sym,
        "three_month_chg_pct": None,
        "sentiment":           "Neutral",
        "warning": (
            f"yfinance data unavailable for {sym}. "
            f"Sentiment defaulted to Neutral — do not weight this in analysis."
        ),
    }
