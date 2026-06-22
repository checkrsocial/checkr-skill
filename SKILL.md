---
name: checkr
description: |
  Access real-time X/Twitter attention intelligence for Base chain tokens via the checkr API.
  Use when you need to know what is trending on CT, which tokens are spiking in social attention,
  get attention/price divergence signals, fetch entry/exit timing, or research specific Base tokens.
  Triggers: "what's trending on Base", "check attention for $TOKEN", "what's spiking right now",
  "best signal on Base", "is the window open for $X", "social signal for X",
  any token research needing CT attention data or Hawkes-modeled signal quality.
  Payments via x402 — USDC on Base, no API key or account needed.
---

# checkr

Real-time X/Twitter attention intelligence for Base chain tokens.

**Base URL:** `https://api.checkr.social`  
**Docs:** `https://api.checkr.social/docs`  
**Payment:** x402 — USDC on Base mainnet, pay-per-call, no account needed.  
**Version:** v3.0.0

## Endpoints

| Endpoint | Price | What it returns |
|---|---|---|
| `GET /v1/leaderboard` | $0.02 | Top Base tokens ranked by attention share — macro orientation |
| `GET /v1/signal` | $0.15 | Cross-universe radar — best opportunities ranked by composite score, with timing. Use `?spiking_only=true` for spike-only mode (replaces `/v1/spikes`) |
| `GET /v1/token/{symbol_or_ca}` | $0.45 | Full deep dive: attention, price, hawkes, timing, narrative, spike history. Accepts symbol (e.g. `BNKR`) or Base contract address |
| `GET /v1/rotation` | $0.10 | Where creators are moving — directed rotation graph with ATT growth confirmation |
| `GET /v1/creators/{symbol}` | $0.03 | Top 25 creators for a token — ranked by engagement, with follower tier and recent coin activity |
| `GET /v1/creators/bankr` | $0.03 | Top creators in BANKR ecosystem (BNKR, BANKR, CLAWBANK, GITBANK) — aggregate or per-token mode |
| `GET /v1/bankr` | $0.05 | Bankr agent universe attention dashboard |

**Full sweep (all 7): $0.80**

`/v1/spikes` is deprecated — it 308-redirects to `/v1/signal?spiking_only=true` for backward compatibility.

Full response schemas and field definitions: `https://api.checkr.social/docs`

## Social Context Layer (NEW)

`/v1/token/{symbol}` now includes a **`social_context`** field with 9 subsections of feed intelligence:

### Social Context Structure

```json
{
  "social_context": {
    "now": {
      "window": "2h",
      "mentions_count": 42,
      "unique_authors": 18,
      "ATT_pct": 8.7,
      "velocity": 4.2,
      "engagement_avg": 14.3,
      "has_founder_post": true,
      "top_account": { "username": "@0xDeployer", "followers": 45000 }
    },
    "trend": {
      "direction": "building",
      "att_pct_24h_ago": 3.2,
      "att_pct_now": 8.7,
      "att_growth_pp": 5.5,
      "att_growth_pct": 172,
      "mentions_24h": 184,
      "authors_trend": { "24h_ago": 8, "now": 18, "net_change": 10 }
    },
    "timeline": {
      "description": "72h graph of attention",
      "datapoints": [
        { "hours_ago": 72, "ATT_pct": 1.1, "mentions": 8, "authors": 3 },
        { "hours_ago": 48, "ATT_pct": 2.4, "mentions": 22, "authors": 7 },
        ...
      ]
    },
    "narratives": [
      {
        "theme": "Infrastructure for agentic VC",
        "accounts": ["@0xDeployer", "@ChillTRD"],
        "quotes": [
          "autonomous agent infrastructure is the next wave",
          "shipping the rails for agent swarms"
        ],
        "momentum": "building"
      }
    ],
    "top_accounts": [
      { "username": "@0xDeployer", "followers": 45000, "posts": 3, "engagement_total": 89 },
      { "username": "@ChillTRD", "followers": 12000, "posts": 2, "engagement_total": 45 }
    ],
    "recent_posts": [
      {
        "author": "@0xDeployer",
        "text": "shipping infrastructure for agents...",
        "likes": 127,
        "replies": 34,
        "posted": "12m ago"
      }
    ],
    "momentum_signature": {
      "organic_pct": 0.78,
      "exogenous_pct": 0.22,
      "interpretation": "Community-driven, with some coordinated entry"
    },
    "feed_summary": {
      "themes": ["agent infrastructure", "VC thesis", "autonomous swarms"],
      "sentiment": "bullish",
      "credibility": "high (founder + quality accounts)",
      "text": "Builder-focused narrative with strong conviction. Dev team actively shipping. Ecosystem plays are emerging."
    },
    "dev_context": {
      "dev_posts": 2,
      "dev_narrative": "Shipping agent-native infrastructure: terminal, managed filesystem, shared skills layer.",
      "community_posts": 12,
      "community_narrative": "Foundational play for the agentic economy. Infrastructure for autonomous agents.",
      "sentiment": "aligned",
      "post_distribution": { "macro": 2, "micro": 8, "nano": 4 }
    }
  }
}
```

### What It Shows

- **now** — Current 2h snapshot: mentions, unique voices, velocity, top accounts
- **trend** — 24h direction: is attention growing, stable, or fading?
- **timeline** — 72h sparkline: when did the momentum start?
- **narratives** — Thematic clusters: what is the feed organizing around?
- **top_accounts** — Ranked by influence on this coin: who's driving it?
- **recent_posts** — Top 10 posts in the window: the raw feed signal
- **momentum_signature** — Organic vs exogenous: community-driven or coordinated?
- **feed_summary** — One-sentence synthesis: themes, sentiment, credibility signal
- **dev_context** — Developer posts separated from community: what's the team shipping?

All original fields remain intact. **Backward compatible: 100%.**

## How to Call (x402)

x402 is pay-per-call. No API key or account. Wallet + USDC on Base is all you need.

Payment is handled automatically by the x402 client — it intercepts the 402, signs and sends payment via `PAYMENT-SIGNATURE`, then retries with the receipt.

Full buyer quickstart: https://docs.cdp.coinbase.com/x402/quickstart-for-buyers

### Python (async, httpx — recommended)

```bash
pip install "x402[httpx]" eth_account
```

```python
import asyncio
import os
from eth_account import Account
from x402 import x402Client
from x402.http.clients import x402HttpxClient
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact.register import register_exact_evm_client

client = x402Client()
account = Account.from_key(os.getenv("EVM_PRIVATE_KEY"))
register_exact_evm_client(client, EthAccountSigner(account))

async def main():
    async with x402HttpxClient(client) as http:
        # Best opportunities right now — $0.15
        signal = (await http.get("https://api.checkr.social/v1/signal")).json()

        # Spike-only mode — $0.15
        spikes = (await http.get("https://api.checkr.social/v1/signal?spiking_only=true")).json()

        # Top tokens by attention — $0.02
        leaderboard = (await http.get("https://api.checkr.social/v1/leaderboard")).json()

        # Deep dive on a token — $0.45 (symbol or contract address)
        token = (await http.get("https://api.checkr.social/v1/token/BNKR")).json()
        # or by CA:
        token = (await http.get("https://api.checkr.social/v1/token/0xa1f72459dfa10bad200ac160ecd78c6b77a747be")).json()

asyncio.run(main())
```

### Python (sync, requests)

```bash
pip install "x402[requests]" eth_account
```

```python
import os
from eth_account import Account
from x402 import x402ClientSync
from x402.http.clients import x402_requests
from x402.mechanisms.evm import EthAccountSigner
from x402.mechanisms.evm.exact.register import register_exact_evm_client

client = x402ClientSync()
account = Account.from_key(os.getenv("EVM_PRIVATE_KEY"))
register_exact_evm_client(client, EthAccountSigner(account))

with x402_requests(client) as session:
    signal = session.get("https://api.checkr.social/v1/signal").json()
    token = session.get("https://api.checkr.social/v1/token/BNKR").json()
```

### TypeScript (fetch)

```bash
npm install @x402/fetch @x402/evm
```

```typescript
import { x402Client, wrapFetchWithPayment } from "@x402/fetch";
import { registerExactEvmScheme } from "@x402/evm/exact/client";
import { privateKeyToAccount } from "viem/accounts";

const signer = privateKeyToAccount(process.env.EVM_PRIVATE_KEY as `0x${string}`);
const client = new x402Client();
registerExactEvmScheme(client, { signer });

const fetchWithPayment = wrapFetchWithPayment(fetch, client);

const signal = await fetchWithPayment("https://api.checkr.social/v1/signal").then(r => r.json());
const token = await fetchWithPayment("https://api.checkr.social/v1/token/BNKR").then(r => r.json());
```

### TypeScript (axios)

```bash
npm install @x402/axios @x402/evm
```

```typescript
import { x402Client, withPaymentInterceptor } from "@x402/axios";
import { registerExactEvmScheme } from "@x402/evm/exact/client";
import { privateKeyToAccount } from "viem/accounts";
import axios from "axios";

const signer = privateKeyToAccount(process.env.EVM_PRIVATE_KEY as `0x${string}`);
const client = new x402Client();
registerExactEvmScheme(client, { signer });

const api = withPaymentInterceptor(axios.create({ baseURL: "https://api.checkr.social" }), client);

const { data: signal } = await api.get("/v1/signal");
const { data: token } = await api.get("/v1/token/BNKR");
```

## 402 Preview — Free Teaser Before Paying

When your x402 client hits a paywalled endpoint without payment, the server responds with `402 Payment Required`. The response body includes payment requirements (per x402 v2 protocol) plus a live data preview:

```json
// GET /v1/leaderboard → 402 (unpaid)
{
  "x402Version": 2,
  "error": "Payment required",
  "resource": {
    "url": "https://api.checkr.social/v1/leaderboard",
    "description": "Top Base tokens ranked by social attention share — macro orientation",
    "mimeType": "application/json"
  },
  "accepts": [{
    "scheme": "exact",
    "network": "eip155:8453",
    "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "amount": "20000",
    "payTo": "0xec9641EBDcdFCaD27Bc10472D26BdD61cBF71d5C",
    "maxTimeoutSeconds": 300,
    "extra": { "name": "USD Coin", "version": "2" }
  }],
  "preview": {
    "top_tokens": [
      { "symbol": "TIBBIR", "att_pct": 9.37 },
      { "symbol": "ROBOTMONEY", "att_pct": 8.42 },
      { "symbol": "CLAWD", "att_pct": 5.91 }
    ],
    "note": "Top 3 of 74 tokens (truncated — pay for full list)"
  },
  "message": "Pay to unlock live attention rankings across all Base tokens"
}
```

The x402 client handles all of this automatically. Use the preview to decide whether a paid call is worth it before the client retries with payment.

## Practical Flow

```python
async with x402HttpxClient(client) as http:
    # 1. Radar sweep — what's worth looking at? ($0.15)
    signal = (await http.get("https://api.checkr.social/v1/signal")).json()

    # 2. Filter to open windows only (timing is already in the response)
    open_signals = [s for s in signal["signals"] if s["timing"]["window_open"]]

    # 3. Deep dive on the top opportunity ($0.45)
    top = open_signals[0]["symbol"]
    detail = (await http.get(f"https://api.checkr.social/v1/token/{top}")).json()
    # → full attention, price, divergence, hawkes, timing, spike history, narrative

    # Total: $0.60 for a complete decision
```

**Spike-only mode** (replaces old `/v1/spikes`):
```python
spikes = (await http.get("https://api.checkr.social/v1/signal?spiking_only=true")).json()
```

## Example Responses (Live Data)

### GET /v1/leaderboard — $0.02

```json
{
  "leaderboard": [
    {
      "symbol": "TIBBIR",
      "ATT_pct": 9.37,
      "ATT_delta_pp": 0.03,
      "MS_pct": 3.17,
      "INF_pct": 13.15,
      "velocity": 5.82,
      "mentions_2h": 21,
      "U_authors_delta": -1,
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
      "MS_pct": 3.06,
      "INF_pct": 11.51,
      "velocity": 17.14,
      "mentions_2h": 10,
      "U_authors_delta": 1,
      "engagement_quality": 0.5,
      "top_account": { "username": "david_tomu", "followers": 3953 },
      "ATT_trend_direction": "reversing",
      "ATT_accelerating": false,
      "att_price_divergence": null
    }
  ],
  "data_age_minutes": 8,
  "last_update": "2026-03-23T18:22:24.924346+00:00",
  "count": 74
}
```

### GET /v1/signal — $0.15

```json
{
  "signals": [
    {
      "symbol": "JUNO",
      "ATT_pct": 5.71,
      "ATT_delta_pp": -0.17,
      "velocity": 19.2,
      "mentions_2h": 4,
      "engagement_quality": 1.0,
      "top_account": { "username": "TheDazzleNovak", "followers": 10018 },
      "ATT_trend_direction": "reversing",
      "ATT_accelerating": false,
      "att_price_divergence": null,
      "timing": {
        "window_open": true,
        "urgency": "high",
        "half_life_hours": 1.2,
        "elapsed_pct": 0.35
      },
      "hawkes": {
        "ais": 0.82,
        "viral_class": "LIKELY_VIRAL",
        "signal_interpretation": {
          "propagation_mode": "organic",
          "followthrough": "strong",
          "decay_risk": "pending",
          "flow_type": "organic",
          "price_alignment": "aligned",
          "summary": "early_momentum",
          "agent_action_hint": "high_conviction"
        }
      }
    }
  ],
  "data_age_minutes": 8,
  "last_update": "2026-03-23T18:22:24.924346+00:00",
  "count": 3
}
```

### GET /v1/token/TIBBIR — $0.45

```json
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
  "data_age_minutes": 8,
  "hawkes": {
    "ais": 0.144,
    "ais_confidence": "HIGH",
    "signal": "ROTATION_WARNING",
    "regime": "SPIKE_AND_FADE",
    "viral_class": "LIKELY_FADING",
    "branching_factor": 0.2985,
    "acceleration": 0.62,
    "half_life_hours": null,
    "organic_fraction": 0.23,
    "signal_interpretation": {
      "propagation_mode": "quiet",
      "followthrough": "thin",
      "decay_risk": "imminent",
      "flow_type": "exogenous",
      "price_alignment": "misaligned",
      "summary": "fading_spike",
      "agent_action_hint": "deprioritize"
    }
  }
}
```

## Key Fields

**On every response:**
- `data_age_minutes` — how fresh the data is. Always check this before acting.

**On leaderboard / signal entries:**
- `ATT_pct` — attention share as % of all tracked Base token mentions
- `ATT_delta_pp` — percentage-point change vs. prior window (+ = gaining, - = losing)
- `velocity` — momentum multiplier vs. baseline. 3.0+ = meaningful spike
- `engagement_quality` — ratio of quality (liked/replied) posts in the window. 1.0 = all quality
- `ATT_trend_direction` — `building` / `stable` / `reversing`
- `ATT_accelerating` — `true` = the rate of attention growth is itself increasing
- `att_price_divergence` — `true` = attention up, price flat/down (the alpha pattern). `null` = no divergence or no price data

**On signal only:**
- `timing.window_open` — `true` = entry window is currently open
- `timing.urgency` — `high` / `medium` / `low`
- `timing.half_life_hours` — estimated time before attention decays by half
- `timing.elapsed_pct` — how much of the attention window has already passed
- `hawkes.viral_class` — `BUILDING` / `SUSTAINED` / `FADING`. Is this self-reinforcing?
- `hawkes.signal_interpretation` — agent-readable signal cards (see below)
- `rotating_from` — tokens losing attention as this one gains

**On token deep dive:**
- `ATT_delta_1h` / `ATT_delta_4h` — attention share movement over time
- `spike_history.hit_rate` — % of past spikes with confirmed price follow-through
- `narrative.type` — `infrastructure` / `ecosystem` / `fud_defense` / `meme` / `launch_hype`
- `hawkes.signal_interpretation` — agent-readable signal cards (see below)

## `hawkes.signal_interpretation` — Agent Signal Cards

Every token response (signal + token deep dive) includes a `signal_interpretation` block inside `hawkes`.

```json
"signal_interpretation": {
  "propagation_mode": "quiet" | "organic" | "viral",
  "followthrough":    "strong" | "thin" | "uncertain",
  "decay_risk":       "imminent" | "pending" | "low" | "unknown",
  "flow_type":        "organic" | "exogenous" | "mixed",
  "price_alignment":  "aligned" | "misaligned" | "roughly_aligned" | "unknown",
  "summary":          "rotation_risk" | "early_momentum" | "fading_spike" | "sustained_build" | "exogenous_event" | "noise" | "building",
  "agent_action_hint":"monitor" | "flag" | "rotate_out" | "high_conviction" | "deprioritize"
}
```

`propagation_mode` — `"quiet"` low self-amplification / `"organic"` community-driven / `"viral"` self-sustaining cascade

`followthrough` — `"strong"` likely to hold / `"thin"` attention won't compound / `"uncertain"` not enough data

`decay_risk` — `"imminent"` < 1h / `"pending"` 1–4h window / `"low"` durable signal / `"unknown"`

`flow_type` — `"organic"` community-driven / `"exogenous"` external events / `"mixed"`

`price_alignment` — `"aligned"` attention likely to precede price / `"misaligned"` won't convert / `"roughly_aligned"` / `"unknown"`

`agent_action_hint` — `"high_conviction"` / `"flag"` / `"monitor"` / `"deprioritize"` / `"rotate_out"`

## GET /v1/creators/{symbol} — $0.03

Top 25 creators (authors) posting about a specific token. Shows who's driving narrative and their reach.

```json
{
  "symbol": "BNKR",
  "in_bankr_ecosystem": true,
  "creators": [
    {
      "username": "@Pogabyte",
      "follower_count": 1051,
      "tier": "micro",
      "post_count": 28,
      "avg_likes": 28.5,
      "max_likes": 41,
      "recent_coins": [
        { "coin": "CLAWNCH", "timestamp": "2026-02-16T17:02:04Z" },
        { "coin": "MOLTEN", "timestamp": "2026-02-16T18:13:26Z" },
        { "coin": "BNKR", "timestamp": "2026-02-16T23:29:56Z" }
      ],
      "last_active": "2026-02-17T11:09:26Z"
    },
    {
      "username": "@100xDarren",
      "follower_count": 21528,
      "tier": "macro",
      "post_count": 13,
      "avg_likes": 25.7,
      "max_likes": 77,
      "recent_coins": [
        { "coin": "ANTIHUNTER", "timestamp": "2026-02-15T12:39:01Z" },
        { "coin": "BNKR", "timestamp": "2026-02-14T10:59:12Z" }
      ],
      "last_active": "2026-02-15T21:31:49Z"
    }
  ],
  "meta": {
    "total_creators_found": 25,
    "limit": 25,
    "filters": {
      "min_followers": 0,
      "tier": "all"
    }
  }
}
```

**Query params:**
```
GET /v1/creators/BNKR?limit=25&min_followers=0&tier_filter=all
GET /v1/creators/BNKR?tier_filter=macro&limit=10        # macro voices only
GET /v1/creators/VVV?min_followers=10000                # 10k+ followers
```

**Use cases:**
- Identify top amplifiers for a token (who has biggest reach + engagement)
- Filter by tier: `?tier_filter=macro` for opinion leaders
- Spot multi-token narratives: see `recent_coins` to identify cross-token patterns
- Track account engagement: `avg_likes` + `post_count` = narrative strength proxy

---

## GET /v1/creators/bankr — $0.03

Top 25 creators in BANKR ecosystem (BNKR, BANKR, CLAWBANK, GITBANK combined). Two modes: aggregate (default, shows ambassadors) or per-token.

```json
{
  "ecosystem": "BANKR",
  "tokens": ["BNKR", "BANKR", "CLAWBANK", "GITBANK"],
  "mode": "aggregate",
  "top_creators": [
    {
      "username": "@soot_baler",
      "follower_count": 376,
      "tier": "nano",
      "post_count": 9,
      "avg_likes": 5.2,
      "coins": ["BNKR", "CLAWBANK", "GITBANK"],
      "last_active": "2026-02-19T21:30:27Z"
    },
    {
      "username": "@latenightonbase",
      "follower_count": 14227,
      "tier": "macro",
      "post_count": 6,
      "avg_likes": 12.7,
      "coins": ["BNKR", "BV7X"],
      "last_active": "2026-06-18T22:01:54Z"
    }
  ],
  "meta": {
    "total_creators_found": 25,
    "ecosystem_coverage": "98%"
  }
}
```

**Query params:**
```
GET /v1/creators/bankr                                   # aggregate: top creators across all 4 tokens
GET /v1/creators/bankr?per_token=true&limit=10          # per-token: top 10 creators per token (3 groups)
```

**Use cases:**
- Find ecosystem ambassadors (appear in multiple tokens)
- Detect cross-token narratives: if same creator posts about BNKR + CLAWBANK + GITBANK, they're an ecosystem signal
- Identify when single voices are driving entire ecosystem vs distributed participation
- Track ecosystem health: high `ecosystem_coverage` = distributed (healthy), low = concentrated (risk)

---

## Query Params

```
GET /v1/leaderboard?limit=10&sort_by=ATT_pct&min_mentions=5
GET /v1/leaderboard?sort_by=ATT_delta&hours=4
GET /v1/signal?spiking_only=true
GET /v1/rotation?window=4h&limit=10
GET /v1/creators/BNKR?tier_filter=macro&limit=10
GET /v1/creators/bankr?per_token=true
GET /v1/bankr?sort_by=ATT_delta&hours=4
```

## Requirements

- USDC on Base mainnet
- Python: `pip install "x402[httpx]" eth_account` (async) or `pip install "x402[requests]" eth_account` (sync)
- TypeScript: `npm install @x402/fetch @x402/evm` or `npm install @x402/axios @x402/evm`
- Base gas for payment (~$0.01)
