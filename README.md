# 📊 EntityIQ MCP

[![MCP Registry](https://img.shields.io/badge/MCP_Registry-active-brightgreen)](https://registry.modelcontextprotocol.io)
[![Railway](https://img.shields.io/badge/Railway-deployed-blueviolet)](https://entityiq-mcp-production.up.railway.app)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue)](https://github.com/gpavan1992/EntityIQ-MCP)

A [Model Context Protocol](https://modelcontextprotocol.io) server for institutional-grade business intelligence — SEC filings, company financials, macroeconomic indicators, FX rates, securities metadata, and country profiles. All from globally trusted free APIs with zero API keys required.

> Built because no MCP server exists that unifies SEC EDGAR, World Bank, OpenFIGI, and country data in one place.

## ⚡ Public Endpoint (no setup required)

MCP endpoint: https://entityiq-mcp-production.up.railway.app

---

## Tools (8)

### 🏢 SEC & Company Intelligence — SEC EDGAR

| Tool | Description |
|---|---|
| `lookup_company` | Find US public companies by name → CIK, ticker, SEC profile URL |
| `get_company_profile` | Company SIC, state of incorporation, fiscal year, recent filings |
| `get_company_financials` | Revenue, net income, assets — historical XBRL data (up to 20 years) |
| `search_sec_filings` | Full-text search across all 10-K, 10-Q, and 8-K filings |

### 🌍 Macroeconomics — World Bank Open Data

| Tool | Description |
|---|---|
| `get_macro_indicators` | GDP, inflation, unemployment, FDI, trade — any country (1960–present) |

### 💱 Foreign Exchange — open.er-api.com + ECB

| Tool | Description |
|---|---|
| `get_fx_rates` | Live and historical FX rates for 160+ currencies |

### 🔐 Securities & Identifiers — OpenFIGI

| Tool | Description |
|---|---|
| `get_security_info` | Ticker → FIGI, security type, market sector (batch up to 10) |

### 🗺️ Country Intelligence — REST Countries

| Tool | Description |
|---|---|
| `get_country_profile` | Capital, currencies, languages, timezone, TLD, borders, flag |

---

## Integration

### Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

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

## Example Prompts

Once connected, ask your AI agent:

- *"Look up Tesla's SEC filings and show me revenue for the last 5 years"*
- *"Search 10-K filings mentioning 'climate risk' — which companies come up?"*
- *"Compare India and Germany's GDP, inflation, and unemployment 2015–2023"*
- *"What's the live USD to EUR, GBP, INR, and JPY rate?"*
- *"Get FIGI identifiers for Apple, Microsoft, and Nvidia"*
- *"Show me Brazil's country profile — currency, languages, timezone, TLD"*
- *"What's Microsoft's net income trend from 2020 to 2024?"*
- *"Find all companies filing 10-Ks mentioning 'AI' or 'machine learning' in 2023"*
- *"Compare US unemployment rate vs India's trend since 2015"*

---

## Data Sources

| Domain | Source | License | Key Required |
|---|---|---|---|
| SEC Filings | [SEC EDGAR](https://www.sec.gov/developer) | Public Domain | No |
| Company Financials | [SEC EDGAR XBRL](https://www.sec.gov/developer) | Public Domain | No |
| Macroeconomics | [World Bank Open Data](https://data.worldbank.org) | CC BY 4.0 | No |
| FX Rates (Live) | [open.er-api.com](https://open.er-api.com) | Open | No |
| FX Rates (Historical) | [Frankfurter / ECB](https://api.frankfurter.dev) | ODbL | No |
| Securities IDs | [OpenFIGI](https://www.openfigi.com) | CC BY 4.0 | No (25 req/min free) |
| Country Data | [REST Countries](https://restcountries.com) | MPL 2.0 | No |

---

## Notes

- All tools support structured JSON responses for agent pipelines
- SEC EDGAR rate limit: ~10 requests/second (recommended)
- OpenFIGI free tier: 25 requests/minute without a key
- World Bank data lags 1–2 years for some indicators
- FX historical rates available back to 1999 (ECB data)
- No API keys required for any data source

---

## License

MIT — built by [Pavan Kumar Galiveeti](https://www.linkedin.com/in/pavan-kumar-galiveeti-a44335192/)
# Updated Sun May 17 18:37:14 IST 2026
# Fresh deploy Sun May 17 22:20:33 IST 2026
