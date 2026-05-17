# EntityIQ MCP

**Public business intelligence, agent-ready.**

EntityIQ is an open-source MCP server that gives AI agents structured access to company filings, financial data, macroeconomic indicators, FX rates, securities metadata, and country profiles — all from free, no-auth public APIs.

Zero API keys. Zero cost to run. Deploy in minutes.

---

## Tools (8)

| Tool | What it does | Source |
|------|-------------|--------|
| `lookup_company` | Find US public companies by name → CIK, ticker | SEC EDGAR |
| `get_company_profile` | SIC, state of incorporation, fiscal year, recent filings | SEC EDGAR |
| `get_company_financials` | Revenue, net income, assets, equity — historical XBRL data | SEC EDGAR |
| `search_sec_filings` | Full-text search across all 10-K/10-Q/8-K filings | SEC EDGAR |
| `get_macro_indicators` | GDP, inflation, unemployment, FDI, trade — any country | World Bank |
| `get_fx_rates` | Live and historical FX rates, 160+ currencies | open.er-api.com + ECB |
| `get_security_info` | Ticker → FIGI, security type, market sector (batch, up to 10) | OpenFIGI |
| `get_country_profile` | Currency, languages, timezone, TLD, population, borders | RestCountries |

---

## Quickstart

\`\`\`bash
git clone https://github.com/yourusername/entityiq-mcp
cd entityiq-mcp
pip install "mcp[cli]>=1.6.0" httpx pydantic
python server.py
\`\`\`

---

## Deploy to Railway

1. Fork this repo
2. Connect to Railway → New Project → Deploy from GitHub
3. Railway auto-detects the Dockerfile
4. Your MCP endpoint: \`https://your-app.railway.app/mcp\`

---

## Data sources

All APIs are free, no keys required:
- SEC EDGAR — US public company filings
- World Bank — Macroeconomic indicators  
- OpenFIGI — Security identifiers
- open.er-api.com — Live FX rates
- Frankfurter/ECB — Historical FX rates
- RestCountries — Country profiles

---

## License

MIT

Built by [Pavan Kumar Galiveeti](https://www.linkedin.com/in/pavan-kumar-galiveeti-a44335192/) · Part of the GlobalPulse / Bharat MCP family.
