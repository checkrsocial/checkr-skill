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

Then ask your agent: *"what's the best signal on Base right now?"* or *"check attention for $BNKR"*

## What you get

- **Signal radar** — cross-universe ranked opportunities with composite scoring (AIS × velocity × cascade × organic flow × historical hit rate)
- **Entry/exit timing** — Hawkes decay math translated into `window_open`, `urgency`, `half_life_hours`, `elapsed_pct`
- **Token deep dive** — full attention, live price, divergence signal, narrative, spike history, Hawkes block, timing — all in one call
- **Leaderboard** — top tokens by attention share, sortable across 1-24h windows
- **Rotation** — directed creator graph: which accounts moved between tokens, with ATT growth confirmation
- **Bankr dashboard** — competitive intelligence for the bankr agent universe
- **signal_interpretation on every endpoint** — 7-field agent-readable block: `propagation_mode`, `followthrough`, `decay_risk`, `flow_type`, `price_alignment`, `summary`, `agent_action_hint`

## How it works

Payments via [x402](https://github.com/coinbase/x402) — pay per call in USDC on Base. No API key, no account, no subscription.

```python
from x402.http import x402_client
import httpx

client = x402_client(
    private_key="0xYOUR_KEY",
    httpx_client=httpx.Client()
)

# radar sweep — best signals right now ($0.15)
signal = client.get("https://api.checkr.social/v1/signal").json()

# filter to open windows, drill into top result ($0.45)
# can pass symbol or contract address
top = next(s for s in signal["signals"] if s["timing"]["window_open"])["symbol"]
token = client.get(f"https://api.checkr.social/v1/token/{top}").json()
# or by CA: token = client.get("https://api.checkr.social/v1/token/0xa1f72459dfa10bad200ac160ecd78c6b77a747be").json()

# full sweep cost: $0.60
```

## Pricing

| Endpoint | Price | Description |
|---|---|---|
| `GET /v1/leaderboard` | $0.02 | Top Base tokens by attention share — macro orientation |
| `GET /v1/signal` | $0.15 | Cross-universe radar — ranked signals with composite scoring and timing |
| `GET /v1/token/{symbol_or_ca}` | $0.45 | Full deep dive: attention, price, hawkes, timing, narrative, spike history (accepts symbol or Base contract address) |
| `GET /v1/rotation` | $0.10 | Directed creator rotation graph with ATT growth confirmation |
| `GET /v1/bankr` | $0.05 | Bankr agent universe attention dashboard |

**Full sweep (all 5): $0.77**

> `/v1/spikes` is deprecated — it redirects (308) to `/v1/signal?spiking_only=true` for backward compatibility.

## Requirements

- Wallet with USDC on Base mainnet
- `pip install x402` (Python) or `npm install x402-axios` (TypeScript)

## Example queries

- *"What's the best signal on Base right now?"*
- *"What's building with an open entry window?"*
- *"Check attention for $BNKR"*
- *"Is $GITLAWB attention diverging from price?"*
- *"Show me tokens where the window is still open"*
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
