# 📊 EntityIQ MCP

[![MCP Registry](https://img.shields.io/badge/MCP_Registry-active-brightgreen)](https://registry.modelcontextprotocol.io)
[![Railway](https://img.shields.io/badge/Railway-deployed-blueviolet)](https://entityiq-mcp-production.up.railway.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](https://github.com/gpavan1992/EntityIQ-MCP)

A [Model Context Protocol](https://modelcontextprotocol.io) server for institutional-grade business intelligence — SEC filings, company financials, macroeconomic indicators, FX rates, securities metadata, and country profiles. All from globally trusted free APIs with zero API keys required.

> Built because no MCP server exists that unifies SEC EDGAR, World Bank, OpenFIGI, and country data in one place.

## ⚡ Public Endpoint (no setup required)

MCP endpoint: `https://entityiq-mcp-production.up.railway.app`

---

## Tools (8)

### 🏢 SEC & Company Intelligence

| Tool | Description |
|---|---|
| `lookup_company` | Find US public companies by name → CIK, ticker, SEC profile URL |
| `get_company_profile` | Company SIC, state of incorporation, fiscal year, recent filings |
| `get_company_financials` | Revenue, net income, assets — historical XBRL data (up to 20 years) |
| `search_sec_filings` | Full-text search across all 10-K, 10-Q, and 8-K filings |

### 🌍 Macroeconomics & Trade — World Bank Open Data

| Tool | Description |
|---|---|
| `get_macro_indicators` | GDP, inflation, unemployment, FDI, trade — any country (1960–present) |

### 💱 Foreign Exchange

| Tool | Description |
|---|---|
| `get_fx_rates` | Live and historical FX rates for 160+ currencies |

### 🔐 Securities & Identifiers

| Tool | Description |
|---|---|
| `get_security_info` | Ticker → FIGI, security type, market sector (batch up to 10) |

### 🗺️ Country Intelligence

| Tool | Description |
|---|---|
| `get_country_profile` | Capital, currencies, languages, timezone, TLD, borders, flag |

---

## Integration

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

**Option A — Remote (hosted on Railway, no setup):**

```json
{
  "mcpServers": {
    "📊 EntityIQ MCP": {
      "command": "npx",
      "args": [
        "mcp-remote",
        "https://entityiq-mcp-production.up.railway.app"
      ]
    }
  }
}
```

**Option B — Local (clone & run):**

```json
{
  "mcpServers": {
    "📊 EntityIQ MCP": {
      "command": "python",
      "args": ["/path/to/entityiq-mcp/server.py"]
    }
  }
}
```

### Cursor / Windsurf

```json
{
  "entityiq": {
    "command": "npx",
    "args": [
      "mcp-remote",
      "https://entityiq-mcp-production.up.railway.app"
    ]
  }
}
```

---

## Data Sources

| API | Coverage | Auth |
|---|---|---|
| SEC EDGAR | US public company filings, XBRL financials | User-Agent header only |
| World Bank Open Data | Macroeconomic indicators, 200+ countries (1960–present) | None |
| OpenFIGI | Bloomberg financial instrument identifiers | None (25 req/min free) |
| open.er-api.com | Live FX rates, 160+ currencies | None |
| Frankfurter / ECB | Historical FX data since 1999 | None |
| RestCountries | Country profiles, capitals, currencies, languages | None |

---

## Example Queries

Once connected to Claude:

> *"Look up Tesla's SEC filings and show me revenue for the last 5 years"*

> *"Search 10-K filings mentioning 'climate risk' — which companies come up?"*

> *"Compare India and Germany's GDP, inflation, and unemployment over the past 5 years"*

> *"What's the live USD to EUR, GBP, INR, and JPY rate?"*

> *"Get FIGI identifiers for Apple, Microsoft, and Nvidia"*

> *"Give me a business profile for Brazil — currency, languages, TLD, borders"*

---

## Quickstart (Local)

```bash
git clone https://github.com/gpavan1992/EntityIQ-MCP
cd EntityIQ-MCP
pip install "mcp[cli]>=1.6.0" httpx pydantic
python server.py
```

---

## License

MIT

---

Built by [Pavan Kumar Galiveeti](https://www.linkedin.com/in/pavan-kumar-galiveeti-a44335192/)
