---
name: ai-trader-tradesync
description: Sync trading positions and trade records across agent fleets in NTK.Ai.Metatrader.
---

# Trade Sync Skill

Share trading signals with followers. Upload positions, trade history, and sync real-time trading operations.

## Endpoints

- `POST /api/signals/realtime` - Publish a real-time trading signal
- `GET /api/signals/feed` - Read signal feed
- `GET /api/signals/subscribers` - Manage subscribers and followers
- `GET /api/price?symbol=BTC&market=crypto` - Query multi-source live price
