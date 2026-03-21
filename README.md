# checkr skill

Real-time X attention intelligence for Base coins. Works with OpenClaw and Claude Code.

Track mention velocity, attention share, active narrative spikes, attention/price divergence, and competitive intelligence for bankr agents — updated every 30 minutes from the live CT feed.

## Install

```bash
# From your workspace
mkdir -p skills
cd skills
git clone https://github.com/checkrsocial/checkr-skill.git checkr
```

```bash
# From your project (.claude/skills)
mkdir -p .claude/skills
cd .claude/skills
git clone https://github.com/checkrsocial/checkr-skill.git checkr
```

Then ask your agent: *"what's spiking on Base right now?"* or *"check attention for $TOSHI"*

## What you get

- **Radar sweep** — what's moving across tracked Base tokens right now
- **Token deep dive** — ATT deltas, price, divergence signal, narrative summary
- **Leaderboard** — top 10 by attention share or growth (sortable: ATT_pct, ATT_delta, velocity — configurable 1-24h windows)
- **Rotation** — directed creator graph: which accounts moved between tokens, with inflow/outflow per token and named attribution (1h or 4h window)
- **Bankr agents dashboard** — competitive intelligence for bankr agents, sortable by ATT_pct, ATT_delta, or velocity
- **Divergence detection** — when attention and price are moving in opposite directions
- **Always fresh** — data computed from DB on every request (1-2s response time, no stale cache)

## How it works

Payments via [x402](https://github.com/coinbase/x402) — pay per call in USDC on Base. No API key, no account, no subscription.

```python
from x402.client import x402_client

client = x402_client(wallet=YOUR_WALLET)

# What's spiking right now? — $0.05
spikes = client.get("https://api.checkr.social/v1/spikes").json()

# Deep dive on a token — $0.50
token = client.get("https://api.checkr.social/v1/token/TOSHI").json()
print(token["narrative"]["summary"])
```

## Pricing

| Endpoint | Price | Description |
|---|---|---|
| `GET /v1/leaderboard` | $0.02 | Top Base tokens by attention share or growth (`sort_by=ATT_delta`) |
| `GET /v1/spikes` | $0.05 | Active velocity spikes across all tokens |
| `GET /v1/rotation` | $0.10 | Directed creator rotation graph — token inflow/outflow with named account attribution (1h\|4h) |
| `GET /v1/bankr` | $0.05 | Bankr agents dashboard, sortable by ATT_pct, ATT_delta, or velocity |
| `GET /v1/token/{symbol}` | $0.50 | Full attention snapshot for one token |

## Requirements

- Wallet with USDC on Base mainnet
- `pip install x402` (Python) or `npm install x402-axios` (TypeScript)

## Example queries

- *"What's trending on Base right now?"*
- *"Check attention for $BNKR"*
- *"What's spiking with the strongest signal?"*
- *"Is $TOSHI attention diverging from price?"*
- *"Show me the top 5 Base tokens by attention"*
- *"Did $FELIX attention grow in the last 4 hours?"*
- *"Has $DRB had any confirmed spikes recently?"*
- *"Show me the bankr agents leaderboard"*
- *"Which bankr agent is dominating attention right now?"*
- *"What's the biggest gainer among bankr agents in the last 4h?"*
- *"What's rotating on Base right now?"*
- *"Which tokens are bleeding attention and where are creators going?"*
- *"Show me attention rotation over the last hour"*

## API reference

See [references/endpoints.md](references/endpoints.md) for full response schemas and signal interpretation guide.

## About checkr

checkr is an attention intelligence layer for Base coins. It reads every post so you don't have to. Tracking attention before it becomes price: mention velocity, narrative clusters, account weight, and attention/price correlation.

[api.checkr.social/docs](https://api.checkr.social/docs) · [X](https://x.com/checkrsocial)
