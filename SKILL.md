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
| `GET /v1/signal` | $0.15 | Cross-universe radar — ranked opportunities with composite scoring, timing, and signal_interpretation |
| `GET /v1/token/{symbol}` | $0.45 | Full deep dive: attention, live price, hawkes, timing, narrative, spike history |
| `GET /v1/rotation` | $0.10 | Directed creator rotation graph with confirmed ATT growth |
| `GET /v1/bankr` | $0.05 | Bankr agent universe attention dashboard |

**Full sweep (all 5): $0.77**

`/v1/spikes` is deprecated — 308 redirects to `/v1/signal?spiking_only=true` for backward compatibility.

Full response schemas and field definitions: `https://api.checkr.social/docs`

## How to Call (x402)

x402 is pay-per-call. No API key or account. Wallet + USDC on Base is all you need.

**Python:**
```python
from x402.http import x402_client
import httpx

client = x402_client(
    private_key="0xYOUR_KEY",
    httpx_client=httpx.Client()
)

# radar sweep — best signals right now ($0.15)
signal = client.get("https://api.checkr.social/v1/signal").json()

# spike-only mode (replaces /v1/spikes) ($0.15)
spikes = client.get("https://api.checkr.social/v1/signal?spiking_only=true").json()

# top tokens by attention — ($0.02)
leaderboard = client.get("https://api.checkr.social/v1/leaderboard").json()

# full deep dive on a token — includes timing ($0.45)
token = client.get("https://api.checkr.social/v1/token/BNKR").json()
```

**TypeScript:**
```typescript
import { withPaymentInterceptor } from "x402-axios";
import axios from "axios";

const client = withPaymentInterceptor(axios.create(), walletClient);

const { data } = await client.get("https://api.checkr.social/v1/signal");
```

Payment is handled automatically by the x402 client — it intercepts the 402, signs and sends payment, then retries with the receipt.

## Practical Flow

```python
# 1. Radar sweep — what's worth looking at? ($0.15)
signal = client.get("https://api.checkr.social/v1/signal").json()

# 2. Filter to tokens with open entry windows (timing is already in the response)
open_signals = [s for s in signal["signals"] if s["timing"]["window_open"]]

# 3. Deep dive on the top opportunity — includes timing, hawkes, price ($0.45)
top = open_signals[0]["symbol"]
detail = client.get(f"https://api.checkr.social/v1/token/{top}").json()
# → full attention, price, divergence, hawkes, timing, spike_history, narrative

# Total: $0.60 for a complete decision
```

## Key Fields

**On every response:**
- `data_age_minutes` — how fresh the data is. Always check before acting.
- `signal_interpretation` — 7-field agent-readable block on every token (see below)

**On /v1/signal entries:**
- `score` — composite signal strength: AIS × velocity_factor × cascade_factor × organic_bonus × history_bonus
- `signal_type` — `spike` | `building` | `divergence`
- `ais` — Attention Intelligence Score (0-1), Hawkes-derived signal quality
- `velocity` — momentum multiplier vs 48h baseline. 3.0+ = confirmed spike
- `cascade_multiplier` — expected total wave size. 2.5 = current mentions will 2.5× before fading
- `timing.window_open` — bool: is the entry window still open?
- `timing.urgency` — `act_now` | `monitor` | `wait` | `passed`
- `timing.elapsed_pct` — % of cascade already played out
- `key_factors` — string array: what's driving the score
- `caution` — string array: flags that temper the signal
- `spike_history.hit_rate` — % of past spikes with confirmed price follow-through

**On /v1/token/{symbol}:**
- `ATT_delta_1h` / `ATT_delta_4h` — attention share movement over time (e.g. "+3.2pp")
- `divergence.detected` — true when attention up, price flat/down
- `timing.peak_attention_in_hours` — estimated hours until attention peaks
- `timing.time_to_90pct_hours` — hours until 90% of cascade completes (practical exit signal)
- `timing.expected_mentions_remaining` — model estimate of mentions before decay
- `hawkes.cascade_multiplier` — expected total wave size
- `hawkes.decay_alpha` — exponential decay rate. High = fades fast. Pair with half_life_hours.
- `hawkes.branching_factor_weighted` — follower-weighted branching. Higher than branching_factor = influential accounts amplifying
- `hawkes.influence_concentration` — 0 = distributed across many accounts. 1 = single whale. High = fragile signal.
- `hawkes.top_competitors` — `[{ symbol, pressure }]` — tokens competing for the same creator attention
- `narrative.summary` — AI-generated 180-char brief. null if below confidence threshold

**signal_interpretation block (on every endpoint):**
```json
{
  "propagation_mode": "quiet | organic | viral",
  "followthrough":    "strong | thin | uncertain",
  "decay_risk":       "imminent | pending | low | unknown",
  "flow_type":        "organic | exogenous | mixed",
  "price_alignment":  "aligned | misaligned | roughly_aligned | unknown",
  "summary":          "rotation_risk | early_momentum | fading_spike | sustained_build | exogenous_event | noise | building",
  "agent_action_hint":"high_conviction | flag | monitor | deprioritize | rotate_out"
}
```

`agent_action_hint` is the key field — an agent can filter on this without parsing any Hawkes math:
- `high_conviction` — strong organic build, likely to sustain and precede price
- `flag` — notable signal, track closely
- `monitor` — watch but don't act yet
- `deprioritize` — fading or noise, move on
- `rotate_out` — attention leaving this token

## Query Params

```
GET /v1/leaderboard?limit=10&sort_by=ATT_pct&hours=4
GET /v1/signal?limit=5&spiking_only=true
GET /v1/signal?divergence_only=true&require_history=true
GET /v1/token/BNKR?hours=4
GET /v1/rotation?window=4h&limit=10&confirmed_only=true
GET /v1/bankr?sort_by=ATT_delta&hours=4
```

## Requirements

- USDC on Base mainnet
- Python: `pip install x402`
- TypeScript: `npm install x402-axios`
- Base gas for payment (~$0.01)
