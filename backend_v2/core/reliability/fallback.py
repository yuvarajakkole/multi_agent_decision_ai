"""
core/reliability/fallback.py
Static fallback data when live APIs fail.
Always labelled source="fallback" so confidence is reduced.
"""

_CODES = {
    "uae": "AE", "dubai": "AE", "abu dhabi": "AE",
    "saudi": "SA", "saudi arabia": "SA",
    "india": "IN", "indonesia": "ID", "singapore": "SG",
    "egypt": "EG", "qatar": "QA", "kuwait": "KW",
    "malaysia": "MY", "nigeria": "NG", "kenya": "KE",
    "south africa": "ZA", "brazil": "BR", "turkey": "TR",
    "uk": "GB", "usa": "US", "germany": "DE",
}

_LENDING  = {"AE":5.4,"SA":6.0,"IN":10.5,"ID":9.5,"SG":3.5,"EG":22.0,"QA":5.5,"KW":4.5,"MY":5.0,"NG":18.0,"KE":12.5,"ZA":8.25,"BR":12.75,"TR":45.0,"GB":5.25,"US":5.33,"DE":4.5}
_GDP      = {"AE":4.2,"SA":2.6,"IN":7.0,"ID":5.1,"SG":2.1,"EG":3.8,"QA":2.4,"KW":2.0,"MY":4.3,"NG":3.3,"KE":5.1,"ZA":0.9,"BR":2.1,"TR":4.5,"GB":0.4,"US":2.5,"DE":0.2}
_INFLATION= {"AE":3.1,"SA":2.4,"IN":5.1,"ID":3.0,"SG":2.4,"EG":28.0,"QA":3.0,"KW":2.8,"MY":2.5,"NG":28.0,"KE":6.0,"ZA":5.3,"BR":4.5,"TR":65.0,"GB":3.2,"US":3.1,"DE":2.9}
_FX_USD   = {"AED":3.67,"SAR":3.75,"INR":83.5,"IDR":15800,"SGD":1.34,"EGP":48.0,"QAR":3.64,"KWD":0.31,"MYR":4.72,"NGN":1550,"KES":129.0,"ZAR":18.5,"BRL":5.0,"TRY":32.0,"GBP":0.79,"EUR":0.92}


def _code(market: str) -> str:
    return _CODES.get(market.lower().strip(), market[:2].upper())


def get_fallback_macro(market: str) -> dict:
    c = _code(market)
    return {
        "source":       "fallback_static",
        "country_code": c,
        "lending_rate": _LENDING.get(c, 8.0),
        "gdp_growth":   _GDP.get(c, 3.5),
        "inflation":    _INFLATION.get(c, 5.0),
        "note":         "Live API unavailable — static benchmark. Verify before use.",
    }


def get_fallback_fx(currency: str) -> dict:
    rate = _FX_USD.get(currency.upper())
    return {"source": "fallback_static", "currency": currency.upper(), "usd_rate": rate,
            "note": "Live FX unavailable — static rate."}


def get_fallback_market_profile(market: str) -> dict:
    return {"source": "fallback_static", "market": market,
            "region": "Emerging Markets", "population": "Unknown", "currency": "Unknown",
            "note": "Live country API unavailable."}
