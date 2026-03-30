"""core/reliability/market_data.py — Static benchmarks when live APIs fail."""

_ISO = {
    "uae":"AE","dubai":"AE","abu dhabi":"AE",
    "saudi":"SA","saudi arabia":"SA","ksa":"SA","riyadh":"SA",
    "india":"IN","mumbai":"IN","delhi":"IN","bangalore":"IN",
    "indonesia":"ID","jakarta":"ID",
    "singapore":"SG",
    "malaysia":"MY","kuala lumpur":"MY",
    "egypt":"EG","cairo":"EG",
    "qatar":"QA","doha":"QA",
    "kenya":"KE","nairobi":"KE",
    "nigeria":"NG","lagos":"NG","abuja":"NG",
    "south africa":"ZA","johannesburg":"ZA",
    "ghana":"GH","accra":"GH",
    "ethiopia":"ET","addis ababa":"ET",
    "tanzania":"TZ","dar es salaam":"TZ",
    "uk":"GB","united kingdom":"GB","london":"GB",
    "usa":"US","united states":"US","new york":"US",
    "germany":"DE","berlin":"DE",
    "brazil":"BR","sao paulo":"BR",
    "turkey":"TR","istanbul":"TR",
    "africa":"NG",   # generic Africa → Nigeria as proxy
}

_MACRO = {
    # code: (lending_rate, gdp_growth, inflation, fintech_maturity, risk_level)
    "AE": (5.4,  4.2, 3.1,  "Developing",  "Low"),
    "SA": (6.0,  2.6, 2.4,  "Developing",  "Low"),
    "IN": (10.5, 7.0, 5.1,  "Mature",      "Medium"),
    "ID": (9.5,  5.1, 3.0,  "Developing",  "Medium"),
    "SG": (3.5,  2.1, 2.4,  "Mature",      "Very Low"),
    "MY": (5.0,  4.3, 2.5,  "Developing",  "Low"),
    "EG": (22.0, 3.8, 28.0, "Emerging",    "Very High"),
    "QA": (5.5,  2.4, 3.0,  "Developing",  "Low"),
    "KE": (12.5, 5.1, 6.0,  "Emerging",    "Medium"),
    "NG": (18.0, 3.3, 28.0, "Emerging",    "High"),
    "ZA": (8.25, 0.9, 5.3,  "Developing",  "Medium"),
    "GH": (27.0, 3.2, 40.0, "Emerging",    "Very High"),
    "ET": (14.0, 6.5, 35.0, "Nascent",     "High"),
    "TZ": (12.0, 5.3, 9.0,  "Nascent",     "Medium"),
    "GB": (5.25, 0.4, 3.2,  "Mature",      "Low"),
    "US": (5.33, 2.5, 3.1,  "Mature",      "Low"),
    "DE": (4.5,  0.2, 2.9,  "Mature",      "Low"),
    "BR": (12.75,2.9, 4.6,  "Developing",  "High"),
    "TR": (45.0, 4.5, 65.0, "Developing",  "Very High"),
}

_MARKET_SIZE = {
    # code: (lending_size, lending_growth, non_lending_size, non_lending_growth, competition)
    "AE": ("$2.5B",  14, "$1.2B",  18, "Medium"),
    "SA": ("$3.0B",  18, "$0.8B",  20, "Medium"),
    "IN": ("$50B",   22, "$8B",    28, "High"),
    "ID": ("$8B",    19, "$2B",    22, "High"),
    "SG": ("$4B",    12, "$3B",    15, "Very High"),
    "MY": ("$2B",    16, "$1B",    18, "Medium"),
    "EG": ("$1.2B",  20, "$0.3B",  25, "Low"),
    "QA": ("$0.8B",  12, "$0.2B",  15, "Low"),
    "KE": ("$0.8B",  20, "$0.4B",  30, "Low"),
    "NG": ("$1.5B",  25, "$0.5B",  30, "Low"),
    "ZA": ("$3B",    14, "$1B",    18, "High"),
    "GH": ("$0.4B",  22, "$0.1B",  25, "Low"),
    "ET": ("$0.3B",  18, "$0.1B",  20, "Very Low"),
    "TZ": ("$0.3B",  20, "$0.1B",  22, "Very Low"),
    "GB": ("$12B",   8,  "$6B",    10, "Very High"),
    "US": ("$200B",  6,  "$80B",   10, "Very High"),
    "DE": ("$15B",   7,  "$5B",    9,  "Very High"),
}

_REGULATORY = {
    "AE": "Supportive",   "SA": "Supportive",   "IN": "Moderate",
    "ID": "Moderate",     "SG": "Supportive",   "MY": "Supportive",
    "EG": "Restrictive",  "QA": "Supportive",   "KE": "Moderate",
    "NG": "Moderate",     "ZA": "Moderate",     "GH": "Moderate",
    "ET": "Restrictive",  "TZ": "Moderate",     "GB": "Supportive",
    "US": "Moderate",     "DE": "Moderate",     "BR": "Moderate",
    "TR": "Restrictive",
}


def iso_code(market: str) -> str:
    return _ISO.get(market.lower().strip(), market[:2].upper())


def get_macro(market: str) -> dict:
    c = iso_code(market)
    d = _MACRO.get(c, (8.0, 3.5, 5.0, "Unknown", "Medium"))
    return {
        "source":          "static_benchmark",
        "country_code":    c,
        "lending_rate":    d[0],
        "gdp_growth":      d[1],
        "inflation":       d[2],
        "fintech_maturity": d[3],
        "macro_risk":      d[4],
    }


def get_market_profile(market: str, product_class: str = "lending") -> dict:
    c = iso_code(market)
    d = _MARKET_SIZE.get(c, ("Unknown", 10, "Unknown", 10, "Medium"))
    if product_class == "lending":
        size, growth = d[0], d[1]
    else:
        size, growth = d[2], d[3]
    return {
        "source":           "static_benchmark",
        "market_size":      size,
        "annual_growth_pct": growth,
        "competition":      d[4],
        "regulatory":       _REGULATORY.get(c, "Unknown"),
    }
