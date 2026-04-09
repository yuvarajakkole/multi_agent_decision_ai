"""
core/reliability/market_data.py

Multi-source market data with honest confidence tracking.

CONTRACT (never violated):
  Every public function returns an envelope dict:
    {
      "data":       {...},          # actual values — None where unavailable
      "source":     str,            # "live_api" | "partial_live" | "static" | "unknown"
      "confidence": float,          # 0.0–1.0  (live=1.0, partial=0.6, static=0.3, unknown=0.0)
      "ignore":     bool,           # True → strategy must skip this agent
      "warnings":   [str],          # every gap/fallback/error is listed here
      "fetched_at": float,          # unix timestamp
    }

Confidence rules (applied in order, multiplicative):
  Live API data:         base 1.00
  Partial live (≥1 ind): base 0.60
  All static:            base 0.30
  Unknown country:       0.00, ignore=True
  Each missing critical field: ×0.80
  Any static field used for critical: ×0.85

  ignore=True when confidence < 0.50 OR source == "unknown"
"""

import logging
import time
from typing import Optional

import requests

log = logging.getLogger("market_data")

# ─── Thresholds ───────────────────────────────────────────────────────────────
CONF_LIVE       = 1.00
CONF_PARTIAL    = 0.60   # some indicators live, some static
CONF_STATIC     = 0.30   # all static
CONF_UNKNOWN    = 0.00   # market not recognised

PENALTY_MISSING_CRITICAL = 0.80   # multiply per missing critical field
PENALTY_STATIC_CRITICAL  = 0.85   # multiply per critical field filled from static

IGNORE_THRESHOLD = 0.50   # confidence below this → ignore=True

CRITICAL_MACRO   = {"lending_rate", "gdp_growth", "inflation"}
CRITICAL_MARKET  = {"market_size", "annual_growth_pct"}

HTTP_TIMEOUT = 8   # seconds per request

# ─── Country resolution — EXACT matches only, no substring tricks ─────────────
# "island" must NOT resolve to "IN" (India).  Unknown → None.

_ISO: dict[str, str] = {
    "uae": "AE", "united arab emirates": "AE", "dubai": "AE", "abu dhabi": "AE",
    "saudi": "SA", "saudi arabia": "SA", "ksa": "SA", "riyadh": "SA",
    "india": "IN", "mumbai": "IN", "delhi": "IN", "bangalore": "IN",
    "bengaluru": "IN", "chennai": "IN", "hyderabad": "IN", "pune": "IN",
    "indonesia": "ID", "jakarta": "ID",
    "singapore": "SG",
    "malaysia": "MY", "kuala lumpur": "MY",
    "egypt": "EG", "cairo": "EG",
    "qatar": "QA", "doha": "QA",
    "kenya": "KE", "nairobi": "KE",
    "nigeria": "NG", "lagos": "NG", "abuja": "NG",
    "south africa": "ZA", "johannesburg": "ZA", "cape town": "ZA",
    "ghana": "GH", "accra": "GH",
    "ethiopia": "ET", "addis ababa": "ET",
    "tanzania": "TZ", "dar es salaam": "TZ",
    "uk": "GB", "united kingdom": "GB", "england": "GB", "london": "GB",
    "usa": "US", "united states": "US", "america": "US", "new york": "US",
    "germany": "DE", "berlin": "DE",
    "brazil": "BR", "sao paulo": "BR",
    "turkey": "TR", "istanbul": "TR", "turkiye": "TR",
    "thailand": "TH", "bangkok": "TH",
    "vietnam": "VN", "hanoi": "VN", "ho chi minh": "VN",
    "philippines": "PH", "manila": "PH",
    "pakistan": "PK", "karachi": "PK", "lahore": "PK",
    "bangladesh": "BD", "dhaka": "BD",
    "sri lanka": "LK", "colombo": "LK",
    "morocco": "MA", "casablanca": "MA",
    "jordan": "JO", "amman": "JO",
    "oman": "OM", "muscat": "OM",
    "bahrain": "BH", "manama": "BH",
    "kuwait": "KW", "kuwait city": "KW",
    "france": "FR", "paris": "FR",
    "spain": "ES", "madrid": "ES",
    "italy": "IT", "rome": "IT",
    "netherlands": "NL", "amsterdam": "NL",
    "sweden": "SE", "stockholm": "SE",
    "canada": "CA", "toronto": "CA",
    "australia": "AU", "sydney": "AU",
    "china": "CN", "beijing": "CN", "shanghai": "CN",
    "japan": "JP", "tokyo": "JP",
    "south korea": "KR", "korea": "KR", "seoul": "KR",
    "hong kong": "HK",
    "taiwan": "TW", "taipei": "TW",
    "new zealand": "NZ", "auckland": "NZ",
    "mexico": "MX", "mexico city": "MX",
    "colombia": "CO", "bogota": "CO",
    "argentina": "AR", "buenos aires": "AR",
    "chile": "CL", "santiago": "CL",
    "peru": "PE", "lima": "PE",
    "rwanda": "RW", "kigali": "RW",
    "senegal": "SN", "dakar": "SN",
    "ivory coast": "CI", "cote d'ivoire": "CI",
    "zambia": "ZM", "lusaka": "ZM",
    "uganda": "UG", "kampala": "UG",
    "cameroon": "CM", "yaounde": "CM",
}


def resolve_iso(market: str) -> Optional[str]:
    """
    Return ISO-2 code or None.
    Never uses market[:2] — that produces garbage ('island'→'IS', 'iran'→'IR').
    Ambiguous or unknown → None.  Caller must handle None.
    """
    if not market or not market.strip():
        return None
    key = market.strip().lower()
    if key in _ISO:
        return _ISO[key]
    # Single unambiguous prefix match (≥4 chars only)
    if len(key) >= 4:
        hits = {code for name, code in _ISO.items() if name.startswith(key)}
        if len(hits) == 1:
            return hits.pop()
    return None


# kept for backward compat with market_agent/tools.py which imports iso_code
def iso_code(market: str) -> str:
    """Backward-compat wrapper. Returns 'UNKNOWN' instead of garbage."""
    result = resolve_iso(market)
    return result if result is not None else "UNKNOWN"


# ─── Static reference tables (last resort — always declared as such) ──────────

_STATIC_MACRO: dict[str, dict] = {
    "AE": {"lending_rate": 5.40,  "gdp_growth": 4.2, "inflation": 3.1,  "fintech_maturity": "Developing", "macro_risk": "Low"},
    "SA": {"lending_rate": 6.00,  "gdp_growth": 2.6, "inflation": 2.4,  "fintech_maturity": "Developing", "macro_risk": "Low"},
    "IN": {"lending_rate": 10.50, "gdp_growth": 7.0, "inflation": 5.1,  "fintech_maturity": "Mature",     "macro_risk": "Medium"},
    "ID": {"lending_rate": 9.50,  "gdp_growth": 5.1, "inflation": 3.0,  "fintech_maturity": "Developing", "macro_risk": "Medium"},
    "SG": {"lending_rate": 3.50,  "gdp_growth": 2.1, "inflation": 2.4,  "fintech_maturity": "Mature",     "macro_risk": "Very Low"},
    "MY": {"lending_rate": 5.00,  "gdp_growth": 4.3, "inflation": 2.5,  "fintech_maturity": "Developing", "macro_risk": "Low"},
    "EG": {"lending_rate": 22.00, "gdp_growth": 3.8, "inflation": 28.0, "fintech_maturity": "Emerging",   "macro_risk": "Very High"},
    "QA": {"lending_rate": 5.50,  "gdp_growth": 2.4, "inflation": 3.0,  "fintech_maturity": "Developing", "macro_risk": "Low"},
    "KE": {"lending_rate": 12.50, "gdp_growth": 5.1, "inflation": 6.0,  "fintech_maturity": "Emerging",   "macro_risk": "Medium"},
    "NG": {"lending_rate": 18.00, "gdp_growth": 3.3, "inflation": 28.0, "fintech_maturity": "Emerging",   "macro_risk": "High"},
    "ZA": {"lending_rate": 8.25,  "gdp_growth": 0.9, "inflation": 5.3,  "fintech_maturity": "Developing", "macro_risk": "Medium"},
    "GH": {"lending_rate": 27.00, "gdp_growth": 3.2, "inflation": 40.0, "fintech_maturity": "Emerging",   "macro_risk": "Very High"},
    "ET": {"lending_rate": 14.00, "gdp_growth": 6.5, "inflation": 35.0, "fintech_maturity": "Nascent",    "macro_risk": "High"},
    "TZ": {"lending_rate": 12.00, "gdp_growth": 5.3, "inflation": 9.0,  "fintech_maturity": "Nascent",    "macro_risk": "Medium"},
    "GB": {"lending_rate": 5.25,  "gdp_growth": 0.4, "inflation": 3.2,  "fintech_maturity": "Mature",     "macro_risk": "Low"},
    "US": {"lending_rate": 5.33,  "gdp_growth": 2.5, "inflation": 3.1,  "fintech_maturity": "Mature",     "macro_risk": "Low"},
    "DE": {"lending_rate": 4.50,  "gdp_growth": 0.2, "inflation": 2.9,  "fintech_maturity": "Mature",     "macro_risk": "Low"},
    "BR": {"lending_rate": 12.75, "gdp_growth": 2.9, "inflation": 4.6,  "fintech_maturity": "Developing", "macro_risk": "High"},
    "TR": {"lending_rate": 45.00, "gdp_growth": 4.5, "inflation": 65.0, "fintech_maturity": "Developing", "macro_risk": "Very High"},
    "TH": {"lending_rate": 4.00,  "gdp_growth": 3.2, "inflation": 2.8,  "fintech_maturity": "Developing", "macro_risk": "Low"},
    "VN": {"lending_rate": 7.50,  "gdp_growth": 6.0, "inflation": 3.5,  "fintech_maturity": "Emerging",   "macro_risk": "Medium"},
    "PH": {"lending_rate": 6.50,  "gdp_growth": 5.5, "inflation": 4.0,  "fintech_maturity": "Emerging",   "macro_risk": "Medium"},
    "PK": {"lending_rate": 21.00, "gdp_growth": 2.5, "inflation": 26.0, "fintech_maturity": "Emerging",   "macro_risk": "Very High"},
    "BD": {"lending_rate": 9.00,  "gdp_growth": 6.5, "inflation": 9.0,  "fintech_maturity": "Emerging",   "macro_risk": "Medium"},
    "MA": {"lending_rate": 5.50,  "gdp_growth": 3.1, "inflation": 3.5,  "fintech_maturity": "Emerging",   "macro_risk": "Low"},
    "JO": {"lending_rate": 8.50,  "gdp_growth": 2.3, "inflation": 4.0,  "fintech_maturity": "Emerging",   "macro_risk": "Medium"},
    "OM": {"lending_rate": 5.50,  "gdp_growth": 1.5, "inflation": 2.5,  "fintech_maturity": "Developing", "macro_risk": "Low"},
    "KW": {"lending_rate": 4.50,  "gdp_growth": 2.0, "inflation": 2.8,  "fintech_maturity": "Developing", "macro_risk": "Low"},
    "RW": {"lending_rate": 9.00,  "gdp_growth": 7.2, "inflation": 6.0,  "fintech_maturity": "Emerging",   "macro_risk": "Medium"},
}

_STATIC_MARKET: dict[str, dict] = {
    "AE": {"ls": "$2.5B", "lg": 14, "ns": "$1.2B", "ng": 18, "comp": "Medium"},
    "SA": {"ls": "$3.0B", "lg": 18, "ns": "$0.8B", "ng": 20, "comp": "Medium"},
    "IN": {"ls": "$50B",  "lg": 22, "ns": "$8B",   "ng": 28, "comp": "High"},
    "ID": {"ls": "$8B",   "lg": 19, "ns": "$2B",   "ng": 22, "comp": "High"},
    "SG": {"ls": "$4B",   "lg": 12, "ns": "$3B",   "ng": 15, "comp": "Very High"},
    "MY": {"ls": "$2B",   "lg": 16, "ns": "$1B",   "ng": 18, "comp": "Medium"},
    "EG": {"ls": "$1.2B", "lg": 20, "ns": "$0.3B", "ng": 25, "comp": "Low"},
    "QA": {"ls": "$0.8B", "lg": 12, "ns": "$0.2B", "ng": 15, "comp": "Low"},
    "KE": {"ls": "$0.8B", "lg": 20, "ns": "$0.4B", "ng": 30, "comp": "Low"},
    "NG": {"ls": "$1.5B", "lg": 25, "ns": "$0.5B", "ng": 30, "comp": "Low"},
    "ZA": {"ls": "$3B",   "lg": 14, "ns": "$1B",   "ng": 18, "comp": "High"},
    "GH": {"ls": "$0.4B", "lg": 22, "ns": "$0.1B", "ng": 25, "comp": "Low"},
    "ET": {"ls": "$0.3B", "lg": 18, "ns": "$0.1B", "ng": 20, "comp": "Very Low"},
    "TZ": {"ls": "$0.3B", "lg": 20, "ns": "$0.1B", "ng": 22, "comp": "Very Low"},
    "GB": {"ls": "$12B",  "lg":  8, "ns": "$6B",   "ng": 10, "comp": "Very High"},
    "US": {"ls": "$200B", "lg":  6, "ns": "$80B",  "ng": 10, "comp": "Very High"},
    "DE": {"ls": "$15B",  "lg":  7, "ns": "$5B",   "ng":  9, "comp": "Very High"},
    "BR": {"ls": "$8B",   "lg": 15, "ns": "$2B",   "ng": 18, "comp": "High"},
    "TR": {"ls": "$5B",   "lg": 12, "ns": "$1.5B", "ng": 15, "comp": "Medium"},
    "TH": {"ls": "$3B",   "lg": 14, "ns": "$1B",   "ng": 16, "comp": "Medium"},
    "VN": {"ls": "$4B",   "lg": 20, "ns": "$0.8B", "ng": 22, "comp": "Medium"},
    "PH": {"ls": "$3B",   "lg": 18, "ns": "$0.7B", "ng": 20, "comp": "Medium"},
    "PK": {"ls": "$2B",   "lg": 15, "ns": "$0.3B", "ng": 18, "comp": "Low"},
    "BD": {"ls": "$1.5B", "lg": 20, "ns": "$0.2B", "ng": 22, "comp": "Low"},
}

_STATIC_REG: dict[str, str] = {
    "AE": "Supportive",  "SA": "Supportive",  "IN": "Moderate",
    "ID": "Moderate",    "SG": "Supportive",  "MY": "Supportive",
    "EG": "Restrictive", "QA": "Supportive",  "KE": "Moderate",
    "NG": "Moderate",    "ZA": "Moderate",    "GH": "Moderate",
    "ET": "Restrictive", "TZ": "Moderate",    "GB": "Supportive",
    "US": "Moderate",    "DE": "Moderate",    "BR": "Moderate",
    "TR": "Restrictive", "TH": "Moderate",    "VN": "Moderate",
    "PH": "Moderate",    "PK": "Restrictive", "BD": "Moderate",
    "MA": "Moderate",    "JO": "Moderate",    "OM": "Supportive",
    "KW": "Supportive",  "RW": "Moderate",
}


# ─── Envelope builder ─────────────────────────────────────────────────────────

def _build_envelope(
    data: dict,
    source: str,          # "live_api" | "partial_live" | "static" | "unknown"
    confidence: float,
    warnings: list[str],
    fetched_at: float,
) -> dict:
    """
    Finalise envelope.  Apply penalties for missing critical fields.
    Set ignore=True when confidence < IGNORE_THRESHOLD or source==unknown.
    """
    # Count missing critical fields in data
    all_critical = CRITICAL_MACRO | CRITICAL_MARKET
    for field in all_critical:
        if field in data and data[field] is None:
            confidence *= PENALTY_MISSING_CRITICAL
            warnings.append(
                f"[MISSING_CRITICAL] {field}=None — confidence penalised ×{PENALTY_MISSING_CRITICAL}"
            )

    confidence = round(max(0.0, min(1.0, confidence)), 4)
    ignore     = (confidence < IGNORE_THRESHOLD) or (source == "unknown")

    log.info(
        "[market_data] envelope  source=%s  confidence=%.3f  ignore=%s  warnings=%d",
        source, confidence, ignore, len(warnings),
    )
    return {
        "data":       data,
        "source":     source,
        "confidence": confidence,
        "ignore":     ignore,
        "warnings":   warnings,
        "fetched_at": fetched_at,
    }


# ─── Live API fetchers ────────────────────────────────────────────────────────

_WB_BASE = (
    "https://api.worldbank.org/v2/country/{code}/indicator/{ind}"
    "?format=json&mrv=3&per_page=3"
)
_WB_INDICATORS: dict[str, str] = {
    "NY.GDP.MKTP.KD.ZG": "gdp_growth",
    "FP.CPI.TOTL.ZG":    "inflation",
    "FR.INR.LEND":       "lending_rate",
    "NY.GDP.PCAP.CD":    "gdp_per_capita_usd",
    "SL.UEM.TOTL.ZS":    "unemployment_pct",
    "BX.TRF.PWKR.DT.GD.ZS": "remittance_pct_gdp",
}


def _fetch_world_bank(iso: str) -> tuple[dict, int, list[str]]:
    """
    Fetch World Bank indicators.
    Returns (data_dict, live_count, warnings).
    live_count = number of indicators successfully fetched live.
    """
    out: dict      = {}
    warnings: list = []
    live_count     = 0

    for ind, key in _WB_INDICATORS.items():
        try:
            r    = requests.get(_WB_BASE.format(code=iso, ind=ind), timeout=HTTP_TIMEOUT)
            r.raise_for_status()
            body = r.json()
            val  = next(
                (e["value"] for e in (body[1] or []) if e.get("value") is not None),
                None,
            )
            if val is not None:
                out[key] = round(float(val), 3)
                live_count += 1
            else:
                out[key] = None
                warnings.append(f"[WB_NO_DATA] {key} ({ind}): API returned no recent values for {iso}")
        except requests.exceptions.Timeout:
            out[key] = None
            warnings.append(f"[WB_TIMEOUT] {key}: request timed out after {HTTP_TIMEOUT}s")
        except Exception as exc:
            out[key] = None
            warnings.append(f"[WB_ERROR] {key}: {type(exc).__name__}: {exc}")

    log.info("[market_data] WB %s live=%d/%d", iso, live_count, len(_WB_INDICATORS))
    return out, live_count, warnings


def _fetch_rest_countries(iso: str) -> tuple[dict, list[str]]:
    """Fetch country profile from REST Countries API (free, no key)."""
    warnings: list = []
    try:
        r = requests.get(
            f"https://restcountries.com/v3.1/alpha/{iso}",
            timeout=HTTP_TIMEOUT,
        )
        r.raise_for_status()
        d          = r.json()[0]
        currencies = list(d.get("currencies", {}).keys())
        return {
            "country_name": d.get("name", {}).get("common", iso),
            "region":       d.get("region"),
            "subregion":    d.get("subregion"),
            "population":   d.get("population"),
            "currency_code": currencies[0] if currencies else None,
        }, warnings
    except requests.exceptions.Timeout:
        warnings.append(f"[RC_TIMEOUT] REST Countries timed out for {iso}")
    except Exception as exc:
        warnings.append(f"[RC_ERROR] REST Countries: {type(exc).__name__}: {exc}")
    return {"country_name": iso, "region": None, "population": None, "currency_code": None}, warnings


def _fetch_fx_rate(currency_code: Optional[str]) -> tuple[Optional[float], list[str]]:
    """Fetch USD exchange rate from open.er-api.com (free tier)."""
    if not currency_code:
        return None, []
    try:
        r = requests.get(
            f"https://open.er-api.com/v6/latest/{currency_code.upper()}",
            timeout=HTTP_TIMEOUT,
        )
        r.raise_for_status()
        d = r.json()
        if d.get("result") == "success":
            rate = d["rates"].get("USD")
            if rate:
                return round(float(rate), 6), []
            return None, [f"[FX_MISSING] USD rate not in response for {currency_code}"]
    except requests.exceptions.Timeout:
        return None, [f"[FX_TIMEOUT] FX rate timed out for {currency_code}"]
    except Exception as exc:
        return None, [f"[FX_ERROR] {type(exc).__name__}: {exc}"]
    return None, [f"[FX_PARSE] Could not parse FX response for {currency_code}"]


# ─── Public functions ─────────────────────────────────────────────────────────

def get_macro(market: str) -> dict:
    """
    Fetch macroeconomic data for a market.

    Priority:
      1. World Bank API (live)  → fills gdp_growth, inflation, lending_rate, gdp_per_capita
      2. REST Countries API     → fills country_name, region, population, currency
      3. FX rate API            → fills exchange_rate_to_usd
      4. Static table           → fills any remaining gaps (labelled in warnings)

    Confidence:
      all 3 critical indicators live  → 1.00
      ≥1 critical live, some static   → 0.60
      all from static                 → 0.30
      unknown country                 → 0.00 + ignore=True
    """
    ts  = time.time()
    iso = resolve_iso(market)

    if iso is None:
        log.warning("[market_data] get_macro: unknown market '%s'", market)
        return _build_envelope(
            data     = {"market": market},
            source   = "unknown",
            confidence = CONF_UNKNOWN,
            warnings = [
                f"[UNKNOWN_MARKET] '{market}' could not be resolved to an ISO code. "
                f"No data available. Strategy must ignore this agent."
            ],
            fetched_at = ts,
        )

    warnings: list[str] = []

    # Source 1 — World Bank
    wb_data, wb_live, wb_warnings = _fetch_world_bank(iso)
    warnings.extend(wb_warnings)

    # Source 2 — REST Countries
    rc_data, rc_warnings = _fetch_rest_countries(iso)
    warnings.extend(rc_warnings)

    # Source 3 — FX rate
    fx_rate, fx_warnings = _fetch_fx_rate(rc_data.get("currency_code"))
    warnings.extend(fx_warnings)

    # Fill gaps in critical fields from static (each gap is logged)
    static_row  = _STATIC_MACRO.get(iso, {})
    static_used: set[str] = set()

    combined = dict(wb_data)   # start with live results

    for field in ("lending_rate", "gdp_growth", "inflation"):
        if combined.get(field) is None:
            static_val = static_row.get(field)
            if static_val is not None:
                combined[field] = static_val
                static_used.add(field)
                warnings.append(
                    f"[STATIC_FALLBACK] {field}: live data unavailable → "
                    f"static benchmark {static_val} used (confidence penalised)"
                )
            else:
                warnings.append(
                    f"[NO_DATA] {field}: neither live nor static data available for {iso}"
                )

    # Non-live fields (always from static — noted, not penalised separately)
    combined["fintech_maturity"] = static_row.get("fintech_maturity", "Unknown")
    combined["macro_risk"]       = static_row.get("macro_risk",       "Unknown")
    combined["country_code"]     = iso
    combined["exchange_rate_usd"] = fx_rate

    # Merge country profile
    combined.update({k: v for k, v in rc_data.items() if v is not None})

    # Determine source label and base confidence
    critical_live = sum(1 for f in ("gdp_growth", "inflation", "lending_rate")
                        if wb_data.get(f) is not None)

    if critical_live >= 3 and not static_used:
        source     = "live_api"
        confidence = CONF_LIVE
    elif critical_live >= 1:
        source     = "partial_live"
        confidence = CONF_PARTIAL
        # Additional penalty: each critical field that came from static
        for _ in static_used.intersection({"lending_rate", "gdp_growth", "inflation"}):
            confidence *= PENALTY_STATIC_CRITICAL
    elif static_row:
        source     = "static"
        confidence = CONF_STATIC
        warnings.append(
            f"[ALL_STATIC] World Bank returned no live data for {iso}. "
            f"All macro values from static benchmarks. Confidence={CONF_STATIC}."
        )
    else:
        source     = "unknown"
        confidence = CONF_UNKNOWN
        warnings.append(f"[NO_STATIC] No static data for {iso} either.")

    return _build_envelope(
        data       = combined,
        source     = source,
        confidence = confidence,
        warnings   = warnings,
        fetched_at = ts,
    )


def get_market_profile(market: str, product_class: str = "lending") -> dict:
    """
    Market size, competition, regulatory profile.

    Source is always static (no public live API for these estimates).
    Confidence = CONF_STATIC (0.30).  Callers must account for this.
    """
    ts  = time.time()
    iso = resolve_iso(market)

    if iso is None:
        return _build_envelope(
            data       = {"market": market},
            source     = "unknown",
            confidence = CONF_UNKNOWN,
            warnings   = [f"[UNKNOWN_MARKET] '{market}' not recognised — no market profile."],
            fetched_at = ts,
        )

    row = _STATIC_MARKET.get(iso)
    if row is None:
        return _build_envelope(
            data       = {"market": market, "country_code": iso},
            source     = "static",
            confidence = CONF_STATIC * 0.5,   # no entry at all → even lower
            warnings   = [
                f"[NO_MARKET_DATA] {iso} not in static market table. "
                f"No size/competition data available."
            ],
            fetched_at = ts,
        )

    is_lending = product_class == "lending"
    data = {
        "country_code":      iso,
        "product_class":     product_class,
        "market_size":       row["ls"] if is_lending else row["ns"],
        "annual_growth_pct": row["lg"] if is_lending else row["ng"],
        "competition":       row["comp"],
        "regulatory":        _STATIC_REG.get(iso, "Unknown"),
    }

    return _build_envelope(
        data       = data,
        source     = "static",
        confidence = CONF_STATIC,
        warnings   = [
            f"[STATIC_DATA] Market size and competition data from static benchmarks "
            f"(last updated manually). Treat as indicative estimates only."
        ],
        fetched_at = ts,
    )


# ─── Backward-compat wrappers used by market_agent/tools.py ──────────────────
# These unwrap the envelope so the tool output is the same shape as before,
# but they log a warning so we can track usage.

def _compat_get_macro(market: str) -> dict:
    """Deprecated compat — returns flat dict, ignores confidence."""
    env = get_macro(market)
    log.warning(
        "[market_data] _compat_get_macro called — confidence %.2f will be ignored by caller",
        env["confidence"],
    )
    d = dict(env["data"])
    d["_source"]     = env["source"]
    d["_confidence"] = env["confidence"]
    d["_ignore"]     = env["ignore"]
    return d


def _compat_get_market_profile(market: str, product_class: str = "lending") -> dict:
    """Deprecated compat — returns flat dict, ignores confidence."""
    env = get_market_profile(market, product_class)
    log.warning(
        "[market_data] _compat_get_market_profile called — confidence %.2f will be ignored",
        env["confidence"],
    )
    d = dict(env["data"])
    d["_source"]     = env["source"]
    d["_confidence"] = env["confidence"]
    d["_ignore"]     = env["ignore"]
    return d
