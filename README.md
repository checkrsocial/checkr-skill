# checkr skill

Real-time X/Twitter attention intelligence for Base chain tokens. Works with OpenClaw and Claude Code.

Track mention velocity, attention share, Hawkes-modeled signal quality, entry/exit timing, and creator rotation — updated every 30 minutes from the live CT feed.

## Install

```bash
# OpenClaw workspace
mkdir -p skills && cd skills
git clone https://github.com/checkrsocial/checkr-skill.git checkr
```

```bash
# Claude Code (.claude/skills)
mkdir -p .claude/skills && cd .claude/skills
git clone https://github.com/checkrsocial/checkr-skill.git checkr
```

Then ask your agent: *"what's spiking on Base right now?"* or *"check attention for $TIBBIR"*

## What you get

- **Radar sweep** — what's moving across tracked Base tokens right now
- **Token deep dive** — ATT deltas, price, divergence signal, narrative summary
- **Leaderboard** — top tokens by attention share or growth (sortable: ATT_pct, ATT_delta, velocity — configurable 1-24h windows)
- **Rotation** — directed creator graph: which accounts moved between tokens, with inflow/outflow per token and named attribution (1h or 4h window)
- **Bankr agents dashboard** — competitive intelligence for bankr agents, sortable by ATT_pct, ATT_delta, or velocity
- **Divergence detection** — when attention and price are moving in opposite directions
- **Free 402 preview** — every paywalled endpoint returns a live teaser in the 402 body before you pay (top 3 tokens, top 2 spikes, or token att_pct/velocity)

## How it works

Payments via [x402](https://docs.cdp.coinbase.com/x402/welcome) — pay per call in USDC on Base. No API key, no account, no subscription.

```python
# pip install "x402[httpx]" eth_account
import asyncio, os
from eth_account import Account
from x402 import x402Client
from x402.http.clients import x402HttpxClient
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact.register import register_exact_evm_client

client = x402Client()
register_exact_evm_client(client, EthAccountSigner(Account.from_key(os.getenv("EVM_PRIVATE_KEY"))))

async def main():
    async with x402HttpxClient(client) as http:
        # Best signals right now — $0.15
        signal = (await http.get("https://api.checkr.social/v1/signal")).json()

        # Deep dive on a token — $0.45
        token = (await http.get("https://api.checkr.social/v1/token/TIBBIR")).json()

asyncio.run(main())
```

```typescript
// npm install @x402/fetch @x402/evm
import { x402Client, wrapFetchWithPayment } from "@x402/fetch";
import { registerExactEvmScheme } from "@x402/evm/exact/client";
import { privateKeyToAccount } from "viem/accounts";

const signer = privateKeyToAccount(process.env.EVM_PRIVATE_KEY as `0x${string}`);
const client = new x402Client();
registerExactEvmScheme(client, { signer });
const fetchWithPayment = wrapFetchWithPayment(fetch, client);

const signal = await fetchWithPayment("https://api.checkr.social/v1/signal").then(r => r.json());
```

## 402 Preview (peek before paying)

Call any paywalled endpoint without payment — the server responds with `402 Payment Required` (x402 v2 protocol). The body includes payment instructions plus a live data teaser:

```json
// GET /v1/leaderboard → 402
{
  "x402Version": 2,
  "error": "Payment required",
  "accepts": [{
    "scheme": "exact",
    "network": "eip155:8453",
    "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "amount": "20000",
    "payTo": "0xec9641EBDcdFCaD27Bc10472D26BdD61cBF71d5C",
    "maxTimeoutSeconds": 300
  }],
  "preview": {
    "top_tokens": [
      { "symbol": "TIBBIR",     "att_pct": 9.37 },
      { "symbol": "ROBOTMONEY", "att_pct": 8.42 },
      { "symbol": "CLAWD",      "att_pct": 5.91 }
    ],
    "note": "Top 3 of 74 tokens (truncated — pay for full list)"
  },
  "message": "Pay to unlock full data"
}
```

The x402 client handles payment automatically — it reads the `PAYMENT-REQUIRED` header, signs and sends payment via `PAYMENT-SIGNATURE`, and retries. Your agent can also inspect the preview before the client pays.

## Example outputs

### What's trending on Base right now?

```json
// GET /v1/leaderboard
{
  "leaderboard": [
    {
      "symbol": "TIBBIR",
      "ATT_pct": 9.37,
      "ATT_delta_pp": 0.03,
      "velocity": 5.82,
      "mentions_2h": 21,
      "engagement_quality": 0.381,
      "top_account": { "username": "AskGigabrain", "followers": 16762 },
      "ATT_trend_direction": "reversing",
      "ATT_accelerating": false,
      "att_price_divergence": null
    },
    {
      "symbol": "ROBOTMONEY",
      "ATT_pct": 8.42,
      "ATT_delta_pp": -0.88,
      "velocity": 17.14,
      "mentions_2h": 10,
      "engagement_quality": 0.5,
      "top_account": { "username": "david_tomu", "followers": 3953 },
      "ATT_trend_direction": "reversing",
      "ATT_accelerating": false,
      "att_price_divergence": null
    },
    {
      "symbol": "CLAWD",
      "ATT_pct": 5.91,
      "ATT_delta_pp": -0.03,
      "velocity": 12.0,
      "mentions_2h": 7,
      "engagement_quality": 0.4286,
      "top_account": { "username": "TheDazzleNovak", "followers": 10018 },
      "ATT_trend_direction": "reversing",
      "ATT_accelerating": false,
      "att_price_divergence": null
    }
  ],
  "data_age_minutes": 8,
  "count": 74
}
```

### What's spiking hardest?

```json
// GET /v1/signal?spiking_only=true  (/v1/spikes redirects here)
{
  "signals": [
    {
      "symbol": "JUNO",
      "ATT_pct": 5.71,
      "velocity": 19.2,
      "mentions_2h": 4,
      "engagement_quality": 1.0,
      "top_account": { "username": "TheDazzleNovak", "followers": 10018 },
      "ATT_trend_direction": "reversing",
      "att_price_divergence": null
    },
    {
      "symbol": "ROBOTMONEY",
      "ATT_pct": 8.42,
      "velocity": 17.14,
      "mentions_2h": 10,
      "engagement_quality": 0.5,
      "top_account": { "username": "david_tomu", "followers": 3953 },
      "ATT_trend_direction": "reversing",
      "att_price_divergence": null
    },
    {
      "symbol": "KELLYCLAUDE",
      "ATT_pct": 5.55,
      "velocity": 12.0,
      "mentions_2h": 5,
      "engagement_quality": 0.6,
      "ATT_trend_direction": "stable",
      "att_price_divergence": null
    }
  ],
  "count": 3,
  "filters": { "min_velocity": 3.0, "min_mentions": 0, "divergence_only": false }
}
```

### Deep dive on a token

```json
// GET /v1/token/TIBBIR
{
  "symbol": "TIBBIR",
  "ATT_pct": 9.37,
  "ATT_delta_pp": 0.03,
  "velocity": 5.82,
  "mentions_2h": 21,
  "engagement_quality": 0.381,
  "ATT_trend_direction": "reversing",
  "ATT_accelerating": false,
  "att_price_divergence": null,
  "top_account": { "username": "AskGigabrain", "followers": 16762 },
  "data_age_minutes": 8
}
```

## Pricing

| Endpoint | Price | Description |
|---|---|---|
| `GET /v1/leaderboard` | $0.02 | Top Base tokens by attention share or growth (`sort_by=ATT_delta`) |
| `GET /v1/signal` | $0.15 | Cross-universe radar — best opportunities with timing. Use `?spiking_only=true` for spike-only mode |
| `GET /v1/rotation` | $0.10 | Directed creator rotation graph with confirmed ATT growth — token inflow/outflow with named account attribution (1h\|4h) |
| `GET /v1/bankr` | $0.05 | Bankr agents dashboard, sortable by ATT_pct, ATT_delta, or velocity |
| `GET /v1/token/{symbol_or_ca}` | $0.45 | Full attention snapshot for one token — accepts symbol or Base contract address |

`/v1/spikes` is deprecated — it 308-redirects to `/v1/signal?spiking_only=true`.

Payments via x402 — USDC on Base mainnet, pay-per-call. No subscription. No API key. Wallet + USDC is all you need.

## Requirements

- Wallet with USDC on Base mainnet
- Python: `pip install "x402[httpx]" eth_account` (async) or `pip install "x402[requests]" eth_account` (sync)
- TypeScript: `npm install @x402/fetch @x402/evm` or `npm install @x402/axios @x402/evm`

## Example queries

- *"What's the best signal on Base right now?"*
- *"What's building with an open entry window?"*
- *"Check attention for $BNKR"*
- *"What's spiking with the strongest signal?"*
- *"Is $TIBBIR attention diverging from price?"*
- *"Show me the top 5 Base tokens by attention"*
- *"Did $CLAWD attention grow in the last 4 hours?"*
- *"Has $JUNO had any confirmed spikes recently?"*
- *"Show me the bankr agents leaderboard"*
- *"Which bankr agent is dominating attention right now?"*
- *"What's the biggest gainer among bankr agents in the last 4h?"*
- *"What's rotating on Base right now?"*
- *"Which bankr agent is dominating attention?"*
- *"Has $TIBBIR had any confirmed spikes recently?"*
- *"What's the cascade size on this spike — is it worth entering?"*

## API reference

Full field definitions, response schemas, and the `signal_interpretation` guide: [api.checkr.social/docs](https://api.checkr.social/docs)

See also [references/endpoints.md](references/endpoints.md) for detailed field tables.

## About checkr

checkr is an attention intelligence layer for Base. It reads every post so you don't have to — tracking attention before it becomes price: mention velocity, Hawkes-modeled cascade dynamics, narrative clusters, account weight, and attention/price correlation.

[api.checkr.social/docs](https://api.checkr.social/docs) · [X](https://x.com/checkrsocial)
