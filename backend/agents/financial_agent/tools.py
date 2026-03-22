import os
import requests
from langchain_core.tools import tool

_COUNTRY_CODES = {
    "uae": "AE", "dubai": "AE", "abu dhabi": "AE",
    "saudi": "SA", "saudi arabia": "SA", "ksa": "SA",
    "india": "IN", "indonesia": "ID", "singapore": "SG",
    "egypt": "EG", "qatar": "QA", "kuwait": "KW",
    "bahrain": "BH", "oman": "OM", "pakistan": "PK",
    "malaysia": "MY", "thailand": "TH", "nigeria": "NG",
    "kenya": "KE", "south africa": "ZA", "brazil": "BR",
    "uk": "GB", "usa": "US", "germany": "DE", "turkey": "TR",
}

def _get_country_code(market: str) -> str:
    return _COUNTRY_CODES.get(market.lower().strip(), market[:2].upper())


@tool
def get_real_macro_indicators(market: str) -> str:
    """
    Fetch real macroeconomic data from World Bank Open API (free, no key needed).
    Returns lending rate, inflation, GDP growth, current account balance.
    Args:
        market: Target country or region e.g. UAE, India
    """
    code = _get_country_code(market)

    indicators = {
        "FR.INR.LEND":       "Lending interest rate (%)",
        "FP.CPI.TOTL.ZG":    "Inflation (%)",
        "NY.GDP.MKTP.KD.ZG": "GDP growth (%)",
        "BN.CAB.XOKA.GD.ZS": "Current account (% GDP)",
        "NY.GDP.PCAP.CD":    "GDP per capita (USD)",
    }

    results = []
    for ind_code, label in indicators.items():
        try:
            url = (
                f"https://api.worldbank.org/v2/country/{code}"
                f"/indicator/{ind_code}?format=json&mrv=2&per_page=2"
            )
            resp = requests.get(url, timeout=8)
            resp.raise_for_status()
            payload = resp.json()

            if len(payload) > 1 and payload[1]:
                for entry in payload[1]:
                    value = entry.get("value")
                    if value is not None:
                        results.append(
                            f"{label}: {round(float(value), 2)} ({entry.get('date','?')})"
                        )
                        break
                else:
                    results.append(f"{label}: N/A")
            else:
                results.append(f"{label}: N/A")

        except Exception as e:
            results.append(f"{label}: unavailable")

    return f"World Bank financials [{market} / {code}]: " + " | ".join(results)


@tool
def get_currency_exchange_rate(base_currency: str, target_currency: str = "USD") -> str:
    """
    Fetch live currency exchange rate from open.er-api.com (free, no key needed).
    Args:
        base_currency: 3-letter code or country name e.g. AED, INR, uae, india
        target_currency: 3-letter code, default USD
    """
    currency_map = {
        "uae": "AED", "dubai": "AED",
        "saudi": "SAR", "saudi arabia": "SAR",
        "india": "INR", "indonesia": "IDR",
        "singapore": "SGD", "egypt": "EGP",
        "qatar": "QAR", "malaysia": "MYR",
        "nigeria": "NGN", "kenya": "KES",
        "uk": "GBP", "turkey": "TRY", "brazil": "BRL",
    }

    base = currency_map.get(base_currency.lower(), base_currency.upper())

    try:
        resp = requests.get(
            f"https://open.er-api.com/v6/latest/{base}",
            timeout=8
        )
        resp.raise_for_status()
        data = resp.json()

        if data.get("result") == "success":
            rates      = data.get("rates", {})
            usd_rate   = rates.get("USD", "N/A")
            eur_rate   = rates.get("EUR", "N/A")
            target_rate = rates.get(target_currency.upper(), "N/A")
            updated    = data.get("time_last_update_utc", "recent")
            stability  = "Stable (pegged)" if base in ["AED", "SAR", "QAR", "BHD"] else "Floating"

            return (
                f"Exchange rate [{base}]: "
                f"1 {base} = {usd_rate} USD | {eur_rate} EUR | "
                f"{target_rate} {target_currency.upper()} | "
                f"Currency: {stability} | Updated: {updated}"
            )
        return f"Exchange rate for {base}: data unavailable"

    except Exception as e:
        return f"Exchange rate [{base}]: fetch error ({e})"


@tool
def get_stock_market_data(market: str) -> str:
    """
    Fetch real stock market index data using yfinance (free, no key needed).
    Returns current level, 3-month high/low, and recent performance.
    Args:
        market: Country or region name e.g. UAE, India, Saudi Arabia
    """
    index_map = {
        "uae":          ("^DFMGI",     "Dubai Financial Market Index"),
        "dubai":        ("^DFMGI",     "Dubai Financial Market Index"),
        "saudi":        ("^TASI",      "Saudi Tadawul (TASI)"),
        "saudi arabia": ("^TASI",      "Saudi Tadawul (TASI)"),
        "india":        ("^NSEI",      "NSE Nifty 50"),
        "indonesia":    ("^JKSE",      "Jakarta Composite"),
        "singapore":    ("^STI",       "Straits Times Index"),
        "malaysia":     ("^KLSE",      "FTSE Bursa Malaysia"),
        "egypt":        ("^EGX30",     "EGX 30 Index"),
        "uk":           ("^FTSE",      "FTSE 100"),
        "usa":          ("^GSPC",      "S&P 500"),
    }

    ticker_symbol, index_name = index_map.get(
        market.lower(), ("^GSPC", "S&P 500 (global proxy)")
    )

    try:
        import yfinance as yf
        hist = yf.Ticker(ticker_symbol).history(period="3mo")

        if hist.empty:
            return f"Stock data for {market}: No data for {ticker_symbol}"

        current   = round(hist["Close"].iloc[-1], 2)
        high      = round(hist["High"].max(), 2)
        low       = round(hist["Low"].min(), 2)
        month_ago = round(hist["Close"].iloc[-22], 2) if len(hist) >= 22 else None

        perf = ""
        if month_ago:
            change = round(((current - month_ago) / month_ago) * 100, 2)
            perf   = f" | 1-month: {change:+.2f}%"

        return (
            f"{index_name} ({ticker_symbol}): "
            f"Current {current:,.2f} | 3mo High {high:,.2f} | 3mo Low {low:,.2f}{perf}"
        )

    except ImportError:
        return f"{market} stock index: install yfinance with: pip install yfinance"
    except Exception as e:
        return f"Stock data for {market} ({ticker_symbol}): error — {e}"


@tool
def calculate_roi_projection(
    market: str,
    budget_usd: float,
    timeline_months: int,
    product_type: str,
) -> str:
    """
    Calculate dynamic ROI projection using real World Bank lending rates as
    cost-of-capital baseline. Applies product-specific spread assumptions.
    Args:
        market: Target country or region
        budget_usd: Planned investment in USD
        timeline_months: Investment horizon in months
        product_type: Type of product e.g. SME lending, invoice financing
    """
    code = _get_country_code(market)

    # Fetch real lending rate from World Bank
    base_lending_rate = None
    rate_source = "estimated"
    try:
        url = (
            f"https://api.worldbank.org/v2/country/{code}"
            f"/indicator/FR.INR.LEND?format=json&mrv=2&per_page=2"
        )
        resp = requests.get(url, timeout=8)
        data = resp.json()
        if len(data) > 1 and data[1]:
            for entry in data[1]:
                if entry.get("value") is not None:
                    base_lending_rate = float(entry["value"])
                    rate_source = "World Bank live"
                    break
    except Exception:
        pass

    if base_lending_rate is None:
        fallback = {
            "AE": 5.4, "SA": 6.0, "IN": 10.5,
            "ID": 9.5, "SG": 3.5, "EG": 22.0,
            "QA": 5.5, "KW": 4.5, "MY": 5.0,
        }
        base_lending_rate = fallback.get(code, 8.0)

    # Product spread above base lending rate
    spreads = {
        "sme": 6.0, "sme lending": 6.0,
        "invoice": 3.0, "invoice financing": 3.0,
        "retail": 8.0, "retail lending": 8.0,
        "personal": 8.0,
    }
    spread = next(
        (v for k, v in spreads.items() if k in product_type.lower()), 5.0
    )
    product_yield  = base_lending_rate + spread
    years          = timeline_months / 12
    net_yield      = product_yield * 0.65 * 0.965  # cost ratio + NPL
    estimated_roi  = round(net_yield * years, 1)
    estimated_irr  = round(net_yield * 0.85, 1)
    payback_months = round((100 / net_yield) * 12) if net_yield > 0 else 999

    return (
        f"ROI Projection [{market} / {product_type}]: "
        f"Base lending rate: {base_lending_rate:.1f}% ({rate_source}) | "
        f"Product yield: {product_yield:.1f}% | "
        f"Net yield (after costs+NPL): {net_yield:.1f}% | "
        f"Est. {timeline_months}m ROI: {estimated_roi:.1f}% | "
        f"Est. IRR: {estimated_irr:.1f}% | "
        f"Payback: ~{payback_months} months | "
        f"Meets 25% ROI: {estimated_roi >= 25} | "
        f"Meets 18% IRR: {estimated_irr >= 18} | "
        f"Budget: ${budget_usd:,.0f}"
    )


@tool
def get_fintech_market_etf(region: str = "global") -> str:
    """
    Fetch real fintech ETF performance data using yfinance (free, no key needed).
    Gives a proxy for fintech sector health and investor sentiment.
    Args:
        region: Region name e.g. global, emerging markets, india, middle east
    """
    etfs = {
        "global":           [("FINX", "Global X FinTech ETF"),
                             ("ARKF", "ARK Fintech Innovation ETF")],
        "emerging":         [("EEM",  "iShares MSCI Emerging Markets ETF")],
        "emerging markets": [("EEM",  "iShares MSCI Emerging Markets ETF")],
        "asia":             [("AAXJ", "iShares MSCI All Country Asia ex Japan")],
        "middle east":      [("KSA",  "iShares MSCI Saudi Arabia ETF")],
        "india":            [("INDA", "iShares MSCI India ETF")],
        "indonesia":        [("EIDO", "iShares MSCI Indonesia ETF")],
    }

    selected = etfs.get(region.lower(), etfs["global"])
    results  = []

    for ticker_symbol, etf_name in selected:
        try:
            import yfinance as yf
            hist = yf.Ticker(ticker_symbol).history(period="1mo")
            if not hist.empty:
                current   = round(hist["Close"].iloc[-1], 2)
                month_ago = round(hist["Close"].iloc[0], 2)
                change    = round(((current - month_ago) / month_ago) * 100, 2)
                results.append(
                    f"{etf_name} ({ticker_symbol}): ${current:.2f} | "
                    f"1-month: {change:+.2f}%"
                )
        except ImportError:
            results.append(f"{etf_name}: install yfinance")
        except Exception as e:
            results.append(f"{etf_name} ({ticker_symbol}): unavailable")

    return "Fintech ETF sentiment: " + " || ".join(results) if results else "ETF data unavailable."