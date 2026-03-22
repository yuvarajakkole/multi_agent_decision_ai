_CODES = {"uae":"AE","dubai":"AE","saudi":"SA","saudi arabia":"SA","india":"IN",
    "indonesia":"ID","singapore":"SG","egypt":"EG","qatar":"QA","malaysia":"MY",
    "uk":"GB","usa":"US","germany":"DE","kenya":"KE","nigeria":"NG",
    "south africa":"ZA","brazil":"BR","turkey":"TR","africa":"NG",
    "ghana":"GH","ethiopia":"ET","tanzania":"TZ"}
_RATES  = {"AE":5.4,"SA":6.0,"IN":10.5,"ID":9.5,"SG":3.5,"EG":22.0,"QA":5.5,
    "MY":5.0,"GB":5.25,"US":5.33,"DE":4.5,"KE":12.5,"NG":18.0,"ZA":8.25,
    "GH":27.0,"ET":14.0,"TZ":12.0}
_GDP    = {"AE":4.2,"SA":2.6,"IN":7.0,"ID":5.1,"SG":2.1,"EG":3.8,"QA":2.4,
    "MY":4.3,"GB":0.4,"US":2.5,"DE":0.2,"KE":5.1,"NG":3.3,"ZA":0.9}
_INFL   = {"AE":3.1,"SA":2.4,"IN":5.1,"ID":3.0,"SG":2.4,"EG":28.0,"QA":3.0,
    "MY":2.5,"GB":3.2,"US":3.1,"DE":2.9,"KE":6.0,"NG":28.0,"ZA":5.3}
_FX     = {"AED":3.67,"SAR":3.75,"INR":83.5,"IDR":15800,"SGD":1.34,"EGP":48.0,
    "QAR":3.64,"MYR":4.72,"GBP":0.79,"EUR":0.92,"KES":129.0,"NGN":1550,"ZAR":18.5}

def code(m): return _CODES.get(m.lower().strip(), m[:2].upper())
def get_fallback_macro(market):
    c=code(market)
    return {"source":"fallback_static","country_code":c,
        "lending_rate":_RATES.get(c,8.0),"gdp_growth":_GDP.get(c,3.5),
        "inflation":_INFL.get(c,5.0),"note":"Live API unavailable — static benchmark"}
def get_fallback_fx(currency):
    return {"source":"fallback_static","currency":currency.upper(),
        "usd_rate":_FX.get(currency.upper()),"note":"Static rate"}
def get_fallback_market_profile(market):
    return {"source":"fallback_static","market":market,"region":"Emerging Markets",
        "population":"Unknown","currency":"Unknown","note":"Country API unavailable"}
