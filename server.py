"""
EntityIQ MCP Server
Public business intelligence — company filings, financials, macro data,
FX rates, securities, geolocation, and country profiles. All from free,
no-auth public APIs. Zero cost to run.
"""

import json
import httpx
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from mcp.server.fastmcp import FastMCP

# ---------------------------------------------------------------------------
# Server
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "entityiq_mcp",
    instructions=(
        "EntityIQ gives you structured access to public business intelligence: "
        "SEC filings, company financials, macro indicators, live FX rates, "
        "securities metadata, country profiles, and geocoding. "
        "All data is sourced from free public APIs with no API keys required. "
        "Start with lookup_company to get a CIK, then use other tools for deeper analysis."
    ),
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SEC_HEADERS = {"User-Agent": "EntityIQ-MCP contact@entityiq.io"}
TIMEOUT = 20.0

WB_INDICATORS = {
    "gdp":            ("NY.GDP.MKTP.CD",       "GDP (current US$)"),
    "gdp_per_capita": ("NY.GDP.PCAP.CD",       "GDP per capita (current US$)"),
    "inflation":      ("FP.CPI.TOTL.ZG",       "Inflation, consumer prices (annual %)"),
    "unemployment":   ("SL.UEM.TOTL.ZS",       "Unemployment, total (% of labor force)"),
    "fdi":            ("BX.KLT.DINV.WD.GD.ZS", "Foreign direct investment (% of GDP)"),
    "trade":          ("NE.TRD.GNFS.ZS",       "Trade (% of GDP)"),
    "population":     ("SP.POP.TOTL",          "Population, total"),
    "exports":        ("NE.EXP.GNFS.ZS",       "Exports of goods and services (% of GDP)"),
    "imports":        ("NE.IMP.GNFS.ZS",       "Imports of goods and services (% of GDP)"),
    "gni":            ("NY.GNP.MKTP.CD",       "GNI (current US$)"),
}

# ---------------------------------------------------------------------------
# Shared HTTP helpers
# ---------------------------------------------------------------------------

async def _get(url: str, params: dict | None = None, headers: dict | None = None) -> dict:
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        r = await client.get(url, params=params, headers=headers or {})
        r.raise_for_status()
        return r.json()


async def _post(url: str, payload: list | dict, headers: dict | None = None) -> list | dict:
    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        r = await client.post(url, json=payload, headers=headers or {})
        r.raise_for_status()
        return r.json()


def _err(msg: str) -> str:
    return json.dumps({"error": msg})


def _ok(data: dict | list) -> str:
    return json.dumps(data, indent=2, default=str)


# ---------------------------------------------------------------------------
# Tool 1 — lookup_company
# ---------------------------------------------------------------------------

class LookupCompanyInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    name: str = Field(..., description="Company name to search (e.g. 'Tesla', 'Apple')", min_length=1, max_length=200)
    limit: Optional[int] = Field(default=5, description="Max matches to return (1-20)", ge=1, le=20)


@mcp.tool(
    name="lookup_company",
    annotations={"title": "Lookup Company by Name", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def lookup_company(params: LookupCompanyInput) -> str:
    """Find US public companies by name and return SEC CIK, ticker, and profile URL.

    The CIK returned here is required by get_company_profile, get_company_financials,
    and search_sec_filings. This is always the first step for SEC-based research.

    Args:
        params (LookupCompanyInput):
            - name (str): Company name fragment to search
            - limit (int): Max results (default 5)

    Returns:
        str: JSON object:
            {
              "query": "Tesla",
              "count": 1,
              "results": [
                {
                  "cik": "0001318605",
                  "ticker": "TSLA",
                  "name": "Tesla, Inc.",
                  "submissions_url": "https://data.sec.gov/submissions/CIK0001318605.json"
                }
              ]
            }
    """
    try:
        data = await _get("https://www.sec.gov/files/company_tickers.json", headers=SEC_HEADERS)
    except Exception as e:
        return _err(f"SEC lookup failed: {e}")

    query = params.name.lower()
    matches = []
    for entry in data.values():
        title = entry.get("title", "")
        if query in title.lower():
            cik_str = str(entry["cik_str"]).zfill(10)
            matches.append({
                "cik": cik_str,
                "ticker": entry.get("ticker", ""),
                "name": title,
                "submissions_url": f"https://data.sec.gov/submissions/CIK{cik_str}.json",
            })
        if len(matches) >= params.limit:
            break

    if not matches:
        return _err(f"No companies found matching '{params.name}'. Try a shorter or different name.")

    return _ok({"query": params.name, "count": len(matches), "results": matches})


# ---------------------------------------------------------------------------
# Tool 2 — get_company_profile
# ---------------------------------------------------------------------------

class CompanyProfileInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    cik: str = Field(..., description="10-digit SEC CIK, zero-padded (e.g. '0000320193'). Get from lookup_company.", min_length=1, max_length=20)


@mcp.tool(
    name="get_company_profile",
    annotations={"title": "Get Company Profile from SEC", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def get_company_profile(params: CompanyProfileInput) -> str:
    """Retrieve full company profile from SEC EDGAR: SIC industry, state of incorporation,
    fiscal year end, business address, and 10 most recent filing dates.

    Args:
        params (CompanyProfileInput):
            - cik (str): 10-digit SEC CIK (get from lookup_company)

    Returns:
        str: JSON object with company metadata and recent filings.
    """
    padded = params.cik.lstrip("0").zfill(10) if params.cik.lstrip("0") else "0000000000"
    try:
        data = await _get(f"https://data.sec.gov/submissions/CIK{padded}.json", headers=SEC_HEADERS)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return _err(f"CIK {params.cik} not found. Use lookup_company to get a valid CIK.")
        return _err(f"SEC request failed: {e}")
    except Exception as e:
        return _err(f"Request failed: {e}")

    recent = data.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    dates = recent.get("filingDate", [])
    accessions = recent.get("accessionNumber", [])
    filings = [
        {"form": forms[i], "filing_date": dates[i], "accession_number": accessions[i]}
        for i in range(min(10, len(forms)))
    ]

    return _ok({
        "name": data.get("name"),
        "cik": padded,
        "ticker": (data.get("tickers") or [""])[0],
        "sic": data.get("sic"),
        "sic_description": data.get("sicDescription"),
        "state_of_incorporation": data.get("stateOfIncorporation"),
        "fiscal_year_end": data.get("fiscalYearEnd"),
        "business_address": data.get("addresses", {}).get("business", {}),
        "recent_filings": filings,
    })


# ---------------------------------------------------------------------------
# Tool 3 — get_company_financials
# ---------------------------------------------------------------------------

class CompanyFinancialsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    cik: str = Field(..., description="10-digit SEC CIK (get from lookup_company)", min_length=1, max_length=20)
    metric: str = Field(
        default="Revenues",
        description=(
            "XBRL financial concept. Common values: 'Revenues', 'NetIncomeLoss', "
            "'Assets', 'Liabilities', 'StockholdersEquity', 'OperatingIncomeLoss', "
            "'EarningsPerShareBasic', 'CashAndCashEquivalentsAtCarryingValue'. Default: 'Revenues'."
        ),
        min_length=1,
        max_length=100,
    )
    form_type: str = Field(default="10-K", description="Filing form: '10-K' (annual) or '10-Q' (quarterly). Default '10-K'.")
    years: Optional[int] = Field(default=5, description="Number of most-recent periods to return (1-20). Default 5.", ge=1, le=20)


@mcp.tool(
    name="get_company_financials",
    annotations={"title": "Get Company Financial Data (SEC XBRL)", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def get_company_financials(params: CompanyFinancialsInput) -> str:
    """Retrieve historical financial data for any US public company from SEC XBRL."""
    padded = params.cik.lstrip("0").zfill(10) if params.cik.lstrip("0") else "0000000000"
    url = f"https://data.sec.gov/api/xbrl/companyconcept/CIK{padded}/us-gaap/{params.metric}.json"

    try:
        data = await _get(url, headers=SEC_HEADERS)
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return _err(f"Metric '{params.metric}' not found for CIK {params.cik}.")
        return _err(f"SEC request failed: {e}")
    except Exception as e:
        return _err(f"Request failed: {e}")

    units = data.get("units", {})
    raw_data = units.get("USD") or units.get("shares") or []
    unit_label = "USD" if "USD" in units else (list(units.keys()) or ["unknown"])[0]

    seen: set = set()
    filtered = []
    for item in raw_data:
        if item.get("form") == params.form_type:
            key = item.get("end")
            if key and key not in seen:
                seen.add(key)
                filtered.append({
                    "period_end": item.get("end"),
                    "value": item.get("val"),
                    "filed": item.get("filed"),
                    "accession": item.get("accn"),
                })

    filtered = filtered[-params.years:]

    return _ok({
        "entity": data.get("entityName"),
        "cik": padded,
        "metric": params.metric,
        "unit": unit_label,
        "form_type": params.form_type,
        "period_count": len(filtered),
        "data": filtered,
    })


# ---------------------------------------------------------------------------
# Tool 4 — search_sec_filings
# ---------------------------------------------------------------------------

class SearchFilingsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    query: str = Field(..., description="Keyword or phrase to search in SEC filing text", min_length=1, max_length=300)
    form_type: Optional[str] = Field(default="10-K", description="SEC form type: '10-K', '10-Q', '8-K', 'DEF 14A', or blank for all.")
    start_date: Optional[str] = Field(default=None, description="Start date filter YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="End date filter YYYY-MM-DD")
    limit: Optional[int] = Field(default=10, description="Max results to return (1-25). Default 10.", ge=1, le=25)


@mcp.tool(
    name="search_sec_filings",
    annotations={"title": "Search SEC EDGAR Full-Text Filings", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def search_sec_filings(params: SearchFilingsInput) -> str:
    """Search the full text of all SEC public filings by keyword or phrase."""
    url = "https://efts.sec.gov/LATEST/search-index"
    query_params: dict = {"q": f'"{params.query}"'}

    if params.form_type:
        query_params["forms"] = params.form_type
    if params.start_date or params.end_date:
        query_params["dateRange"] = "custom"
        if params.start_date:
            query_params["startdt"] = params.start_date
        if params.end_date:
            query_params["enddt"] = params.end_date

    try:
        data = await _get(url, params=query_params, headers=SEC_HEADERS)
    except Exception as e:
        return _err(f"SEC full-text search failed: {e}")

    hits = data.get("hits", {})
    total = hits.get("total", {}).get("value", 0)
    docs = hits.get("hits", [])[:params.limit]

    results = []
    for doc in docs:
        src = doc.get("_source", {})
        display = (src.get("display_names") or [""])[0]
        results.append({
            "company": display,
            "form": src.get("form_type", ""),
            "filed": src.get("file_date", ""),
            "period": src.get("period_of_report", ""),
        })

    return _ok({
        "query": params.query,
        "form_type": params.form_type,
        "total_hits": total,
        "returned": len(results),
        "results": results,
    })


# ---------------------------------------------------------------------------
# Tool 5 — get_macro_indicators
# ---------------------------------------------------------------------------

class MacroIndicatorsInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    country_code: str = Field(..., description="ISO 2-letter country code (e.g. 'US', 'IN', 'DE')", min_length=2, max_length=3)
    indicators: Optional[list[str]] = Field(
        default=None,
        description="Indicators to fetch. Options: gdp, gdp_per_capita, inflation, unemployment, fdi, trade, population, exports, imports, gni. Default: all.",
    )
    years: Optional[int] = Field(default=5, description="Most-recent years to return per indicator (1-20). Default 5.", ge=1, le=20)


@mcp.tool(
    name="get_macro_indicators",
    annotations={"title": "Get Macroeconomic Indicators (World Bank)", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def get_macro_indicators(params: MacroIndicatorsInput) -> str:
    """Retrieve macroeconomic indicators for any country from the World Bank Open Data API."""
    requested = params.indicators or list(WB_INDICATORS.keys())
    invalid = [i for i in requested if i not in WB_INDICATORS]
    if invalid:
        return _err(f"Unknown indicators: {invalid}. Valid: {list(WB_INDICATORS.keys())}")

    country = params.country_code.upper()
    result: dict = {"country": country, "indicators": {}}

    async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
        for key in requested:
            wb_code, label = WB_INDICATORS[key]
            url = (
                f"https://api.worldbank.org/v2/country/{country}"
                f"/indicator/{wb_code}?format=json&per_page={params.years}&mrv={params.years}"
            )
            try:
                r = await client.get(url)
                r.raise_for_status()
                raw = r.json()
                data_points = raw[1] if len(raw) > 1 and raw[1] else []
                entries = [
                    {"year": item["date"], "value": item["value"]}
                    for item in data_points
                    if item.get("value") is not None
                ]
                result["indicators"][key] = {"label": label, "wb_code": wb_code, "data": entries}
            except Exception as e:
                result["indicators"][key] = {"label": label, "error": str(e)}

    return _ok(result)


# ---------------------------------------------------------------------------
# Tool 6 — get_fx_rates
# ---------------------------------------------------------------------------

class FxRatesInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    base: str = Field(default="USD", description="Base currency ISO code (e.g. 'USD', 'EUR', 'INR', 'GBP'). Default 'USD'.", min_length=3, max_length=3)
    targets: Optional[list[str]] = Field(default=None, description="Target currency codes (e.g. ['EUR','GBP','INR']). Leave empty for all ~160 currencies.")
    date: Optional[str] = Field(default=None, description="Date YYYY-MM-DD for historical rates. Leave blank for live rates.")


@mcp.tool(
    name="get_fx_rates",
    annotations={"title": "Get Foreign Exchange Rates", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def get_fx_rates(params: FxRatesInput) -> str:
    """Get live or historical foreign exchange rates for any currency pair."""
    base = params.base.upper()

    try:
        if params.date:
            url = f"https://api.frankfurter.dev/v1/{params.date}"
            query: dict = {"from": base}
            if params.targets:
                query["to"] = ",".join(t.upper() for t in params.targets)
            data = await _get(url, params=query)
            rates = data.get("rates", {})
            source = "historical (ECB via Frankfurter)"
            date_label = data.get("date", params.date)
        else:
            data = await _get(f"https://open.er-api.com/v6/latest/{base}")
            if data.get("result") != "success":
                return _err(f"FX API error: {data.get('error-type', 'unknown')}")
            all_rates = data.get("rates", {})
            rates = (
                {t.upper(): all_rates[t.upper()] for t in params.targets if t.upper() in all_rates}
                if params.targets
                else all_rates
            )
            source = "live (open.er-api.com)"
            date_label = data.get("time_last_update_utc", "")
    except Exception as e:
        return _err(f"FX rates request failed: {e}")

    return _ok({"base": base, "date": date_label, "source": source, "currency_count": len(rates), "rates": rates})


# ---------------------------------------------------------------------------
# Tool 7 — get_security_info
# ---------------------------------------------------------------------------

class SecurityInfoInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    tickers: list[str] = Field(..., description="Ticker symbols to look up (e.g. ['AAPL', 'TSLA', 'MSFT']). Max 10.", min_length=1, max_length=10)
    exchange: Optional[str] = Field(default="US", description="Exchange code: 'US', 'LN', 'GY', 'JP'. Default 'US'.")


@mcp.tool(
    name="get_security_info",
    annotations={"title": "Get Security Metadata (OpenFIGI)", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def get_security_info(params: SecurityInfoInput) -> str:
    """Look up global security identifiers and metadata for ticker symbols via OpenFIGI."""
    tickers = [t.upper() for t in params.tickers[:10]]
    payload = [{"idType": "TICKER", "idValue": ticker, "exchCode": params.exchange} for ticker in tickers]

    try:
        data = await _post("https://api.openfigi.com/v3/mapping", payload=payload, headers={"Content-Type": "application/json"})
    except Exception as e:
        return _err(f"OpenFIGI request failed: {e}")

    results = []
    for ticker, item in zip(tickers, data):
        if "data" in item and item["data"]:
            d = item["data"][0]
            results.append({
                "ticker": ticker,
                "figi": d.get("figi"),
                "name": d.get("name"),
                "security_type": d.get("securityType"),
                "security_type_2": d.get("securityType2"),
                "market_sector": d.get("marketSector"),
                "exchange_code": params.exchange,
            })
        else:
            results.append({"ticker": ticker, "error": item.get("error", "Not found on this exchange")})

    return _ok({"exchange": params.exchange, "results": results})


# ---------------------------------------------------------------------------
# Tool 8 — get_country_profile
# ---------------------------------------------------------------------------

class CountryProfileInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")
    country: str = Field(..., description="Country name (e.g. 'India', 'Germany') or ISO 2-letter code (e.g. 'IN', 'DE')", min_length=2, max_length=100)


@mcp.tool(
    name="get_country_profile",
    annotations={"title": "Get Country Business Profile", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
)
async def get_country_profile(params: CountryProfileInput) -> str:
    """Get a structured business profile for any country."""
    q = params.country.strip()
    if len(q) == 2:
        url = f"https://restcountries.com/v3.1/alpha/{q.lower()}"
    else:
        url = f"https://restcountries.com/v3.1/name/{q}"

    fields = "name,cca2,region,subregion,capital,population,currencies,languages,timezones,tld,flag,borders"

    try:
        data = await _get(f"{url}?fields={fields}")
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return _err(f"Country '{params.country}' not found. Try the full English name or ISO 2-letter code.")
        return _err(f"Request failed: {e}")
    except Exception as e:
        return _err(f"Request failed: {e}")

    c = data[0] if isinstance(data, list) else data
    if not c:
        return _err(f"No country found for '{params.country}'.")

    return _ok({
        "name": c.get("name", {}).get("common"),
        "official_name": c.get("name", {}).get("official"),
        "iso_code": c.get("cca2"),
        "region": c.get("region"),
        "subregion": c.get("subregion"),
        "capital": c.get("capital"),
        "population": c.get("population"),
        "currencies": c.get("currencies", {}),
        "languages": c.get("languages", {}),
        "timezones": c.get("timezones", []),
        "tld": c.get("tld", []),
        "flag": c.get("flag"),
        "borders": c.get("borders", []),
    })


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="streamable_http", port=3000)
