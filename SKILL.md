---
name: checkr
description: |
  Access real-time X/Twitter attention intelligence for Base chain tokens via the checkr API.
  Use when you need to know what is trending on CT, which tokens are spiking in social attention,
  get attention/price divergence signals, or fetch narrative summaries for specific Base tokens.
  Triggers: "what's trending on Base", "check attention for $TOKEN", "what's spiking right now",
  "social signal for X", any token research needing CT attention data.
  Payments via x402 — USDC on Base, no API key or account needed.
---

# checkr API

Real-time X/Twitter attention intelligence for Base chain tokens. Updated every ~30 minutes by the heartbeat pipeline.

**Base URL:** `https://api.checkr.social`  
**Docs:** `https://api.checkr.social/docs`  
**Payment:** x402 — USDC on Base mainnet, pay-per-call, no account needed

## Endpoints

| Endpoint | Price | What it returns |
|---|---|---|
| `GET /v1/leaderboard` | $0.02 | Top 10 Base tokens ranked by social attention share |
| `GET /v1/spikes` | $0.05 | Tokens currently velocity-spiking (radar sweep) |
| `GET /v1/bankr/universe` | $0.05 | Bankr agents competitive intelligence dashboard |
| `GET /v1/token/{symbol}` | $0.50 | Deep dive: ATT deltas, price, divergence, narrative |

See `references/endpoints.md` for full response schemas and examples.

## How to Call (x402)

x402 is pay-per-call HTTP. No API key. Wallet + USDC on Base is all you need.

**Python (recommended):**
```python
from x402.client import x402_client

client = x402_client(wallet=YOUR_WALLET)

# Leaderboard — $0.02
lb = client.get("https://api.checkr.social/v1/leaderboard")

# What's spiking — $0.05
spikes = client.get("https://api.checkr.social/v1/spikes")

# Deep dive — $0.50
token = client.get("https://api.checkr.social/v1/token/FAI")
```

**TypeScript:**
```typescript
import { withPaymentInterceptor } from "x402-axios";
import axios from "axios";
import { createWalletClient } from "viem";

const client = withPaymentInterceptor(axios.create(), walletClient);

const { data } = await client.get("https://api.checkr.social/v1/spikes");
```

Payment is handled automatically by the x402 client — it intercepts the 402 response, signs and sends the payment, then retries with the receipt.

## Practical Flow

Use spikes as your radar, then drill into token for context:

```python
# 1. What's moving right now?
spikes = client.get("https://api.checkr.social/v1/spikes").json()
# → [{ symbol: "FAI", velocity: 4.1, ATT_pct: 9.6, narrative_summary: "..." }]

# 2. Deep dive on the top spike
top = spikes["spikes"][0]["symbol"]
detail = client.get(f"https://api.checkr.social/v1/token/{top}").json()
# → full price, divergence, spike history, narrative
```

## Query Params

- `GET /v1/leaderboard?hours=4&limit=10` — ATT delta over 4h window, top 10
- `GET /v1/spikes?min_velocity=3.0&min_mentions=10` — filter by velocity/mentions

## Data Freshness

All data is pre-computed. No live Twitter API calls at request time. `data_age_minutes` in every response tells you how stale the data is (max ~30 min).

## Requirements

- Wallet with USDC on Base mainnet
- x402 Python client: `pip install x402` or TypeScript: `npm install x402-axios`
- Gas on Base for the payment transaction (typically < $0.01)
