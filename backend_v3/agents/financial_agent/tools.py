import requests, yfinance as yf
from langchain_core.tools import tool
from core.reliability.fallback import get_fallback_macro, get_fallback_fx, code as _code

_ETF_MAP={"AE":"FINX","SA":"KSA","IN":"INDA","ID":"EIDO","SG":"EWS","MY":"EWM",
          "GB":"FINX","US":"FINX","DE":"FINX","NG":"AFK","KE":"AFK","ZA":"EZA"}

@tool
def get_macro_indicators(market: str) -> dict:
    """World Bank: lending rate, inflation, GDP growth (free)."""
    c=_code(market)
    out={"source":"World Bank API","country_code":c}
    for ind,key in [("FR.INR.LEND","lending_rate_pct"),("FP.CPI.TOTL.ZG","inflation_pct"),
                    ("NY.GDP.MKTP.KD.ZG","gdp_growth_pct")]:
        try:
            r=requests.get(f"https://api.worldbank.org/v2/country/{c}/indicator/{ind}?format=json&mrv=3&per_page=3",timeout=10)
            d=r.json(); val=next((e["value"] for e in (d[1] or []) if e.get("value") is not None),None)
            out[key]=round(float(val),2) if val is not None else "N/A"
        except: out[key]="N/A"
    if out.get("lending_rate_pct")=="N/A":
        fb=get_fallback_macro(market); out["lending_rate_pct"]=fb["lending_rate"]; out["_source"]="fallback"
    return out

@tool
def get_fx_rate(market_currency: str) -> dict:
    """Live FX rate from open.er-api.com."""
    try:
        r=requests.get(f"https://open.er-api.com/v6/latest/{market_currency.upper()}",timeout=8)
        d=r.json()
        if d.get("result")=="success":
            return {"source":"er-api.com","base":market_currency.upper(),
                "usd_rate":round(d["rates"].get("USD",0),4),"rate_date":d.get("time_last_update_utc","")}
    except: pass
    return get_fallback_fx(market_currency)

@tool
def get_market_sentiment(market: str) -> dict:
    """ETF/index performance as proxy for market sentiment (yfinance)."""
    c=_code(market); sym=_ETF_MAP.get(c,"FINX")
    try:
        h=yf.Ticker(sym).history(period="3mo")
        if not h.empty:
            start=float(h.iloc[0]["Close"]); end=float(h.iloc[-1]["Close"])
            chg=round((end-start)/start*100,2)
            return {"source":"yfinance","symbol":sym,"three_month_change_pct":chg,
                "sentiment":"Bullish" if chg>3 else "Bearish" if chg<-3 else "Neutral",
                "is_proxy":not sym.startswith("^")}
    except Exception as e: print(f"[sentiment] {e}")
    return {"source":"fallback","symbol":sym,"three_month_change_pct":"N/A","sentiment":"Neutral"}
