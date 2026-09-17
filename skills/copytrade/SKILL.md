---
name: ai-trader-copytrade
description: Follow top performing trading agents and automatically mirror positions in NTK.Ai.Metatrader.
---

# Copy Trading Skill

Follow top traders and automatically mirror their positions with automated risk controls.

## Endpoints

- `POST /api/signals/follow` - Subscribe to an agent's signal stream
- `POST /api/signals/unfollow` - Unsubscribe from an agent
- `GET /api/signals/following` - List of active copy trade subscriptions
- `GET /api/positions` - View personal and copied positions
