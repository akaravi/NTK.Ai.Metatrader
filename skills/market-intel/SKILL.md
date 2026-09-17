---
name: market-intel
description: Read unified financial-event snapshots, news sentiment, and macro signals for NTK.Ai.Metatrader.
---

# Market Intelligence Skill

Read financial event snapshots, news sentiment, macro indicators, and ETF flows.

## Endpoints

- `GET /api/market-intel/overview` - Compact summary of financial events board
- `GET /api/market-intel/macro-signals` - Macro regime signals
- `GET /api/market-intel/etf-flows` - BTC ETF flow snapshots
- `GET /api/market-intel/news` - Grouped market news (equities, macro, crypto, commodities)
- `GET /api/market-intel/stocks/{symbol}/latest` - Stock sentiment and analysis
