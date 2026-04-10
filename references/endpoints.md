# checkr API v3.0.0 — Endpoint Reference

Full field definitions for all 5 endpoints. Live docs: [api.checkr.social/docs](https://api.checkr.social/docs)

---

## GET /v1/leaderboard — $0.02

Macro orientation — top tokens ranked by attention share.

**Params:**

| Param | Values | Default |
|---|---|---|
| `?limit=` | 1–50 | 10 |
| `?hours=` | 1 / 2 / 4 / 8 / 12 / 24 | 4 |
| `?sort_by=` | ATT_pct \| MS_pct \| INF_pct \| velocity \| ATT_delta | ATT_pct |
| `?min_mentions=` | integer | 1 |

**Response fields:**

| Field | Type | Description |
|---|---|---|
| `updated_at` | string | ISO timestamp of last data update |
| `data_age_minutes` | float | Minutes since last heartbeat cycle ran |
| `window_hours` | int | Lookback window used |
| `tokens[].symbol` | string | Token symbol |
| `tokens[].ATT_pct` | float | Composite attention share (%) — AIS-quality-filtered, mindshare + influence weighted |
| `tokens[].MS_pct` | float | Mindshare (%) — engagement-weighted mention share |
| `tokens[].INF_pct` | float | Influence (%) — account-weight-adjusted share |
| `tokens[].ATT_delta` | float | Change in ATT_pct vs prior window (pp). + = gaining, − = losing |
| `tokens[].unique_authors` | int | Distinct accounts posting about this token |
| `tokens[].signal_interpretation` | object | Agent-readable signal block (see signal_interpretation section) |

**Example response:**
```json
{
  "updated_at": "2026-04-10T13:03:01Z",
  "data_age_minutes": 8.2,
  "window_hours": 4,
  "tokens": [
    {
      "symbol": "gitlawb",
      "ATT_pct": 11.8,
      "MS_pct": 7.7,
      "INF_pct": 18.0,
      "ATT_delta": -0.3,
      "unique_authors": 12,
      "signal_interpretation": {
        "propagation_mode": "organic",
        "followthrough": "uncertain",
        "decay_risk": "low",
        "flow_type": "mixed",
        "price_alignment": "roughly_aligned",
        "summary": "building",
        "agent_action_hint": "monitor"
      }
    }
  ]
}
```

---

## GET /v1/signal — $0.15

Cross-universe opportunity radar. Scores every token, returns ranked list with timing. Replaces `/v1/spikes`.

**Params:**

| Param | Values | Default |
|---|---|---|
| `?limit=` | 1–20 | 5 |
| `?min_ais=` | 0.0–1.0 | 0.05 |
| `?min_velocity=` | float | 0.0 |
| `?spiking_only=` | bool | false — shorthand for min_velocity=3.0 |
| `?divergence_only=` | bool | false — only tokens where attention up, price flat/down |
| `?require_history=` | bool | false — only tokens with ≥5 historical spikes |

**Composite score formula:**
```
score = AIS × velocity_factor × cascade_factor × organic_bonus × history_bonus

velocity_factor  = min(velocity / 3.0, 3.0)
cascade_factor   = min(cascade_multiplier / 2.0, 2.0)
organic_bonus    = 1.2 if f_endo > 0.4 else 1.0
history_bonus    = 1.0 + (hit_rate × 0.5) if ≥5 historical spikes else 1.0
```

**Response fields:**

| Field | Type | Description |
|---|---|---|
| `universe_size` | int | Total tokens in tracked universe |
| `signals_found` | int | Tokens passing filters (before limit) |
| `signals[].symbol` | string | Token symbol |
| `signals[].score` | float | Composite signal strength — higher = better opportunity |
| `signals[].rank` | int | Position in ranked list (1 = best) |
| `signals[].signal_type` | string | `spike` / `building` / `divergence` |
| `signals[].ais` | float | Attention Intelligence Score (0–1). Hawkes-derived signal quality. |
| `signals[].velocity` | float | Momentum multiplier vs 48h baseline. 3.0+ = confirmed spike |
| `signals[].att_pct` | float | Current attention share (%) |
| `signals[].ATT_delta_1h` | string | Attention change in last hour (e.g. "+3.2pp") |
| `signals[].cascade_multiplier` | float | Expected total wave size. 2.5 = this spike generates 2.5× current mention count before fading |
| `signals[].half_life_hours` | float\|null | Hours until 50% of cascade plays out. null if unknown |
| `signals[].organic_fraction` | float | Share of posts that are community-driven (0–1). >0.5 = self-reinforcing |
| `signals[].divergence_detected` | bool | true = attention up, price flat/down — the alpha pattern |
| `signals[].spike_history` | object\|null | Historical reliability: `{ confirmed, total, hit_rate }`. null if <5 spikes |
| `signals[].key_factors` | array | 1–3 strings explaining the score (e.g. `"high velocity 7.1×"`, `"proven 52% historical hit rate"`) |
| `signals[].caution` | array | Flags that temper the signal (e.g. `"half_life_under_1h"`, `"exogenous_heavy"`, `"high_influence_concentration"`) |
| `signals[].timing` | object | Compact entry/exit window (see timing fields below) |
| `signals[].signal_interpretation` | object | 7-field agent block (see section) |

**Timing fields (compact, in signal entries):**

| Field | Type | Description |
|---|---|---|
| `window_open` | bool | Is this still worth entering? |
| `entry_quality` | string | `strong` / `moderate` / `weak` / `closed` |
| `urgency` | string | `act_now` / `monitor` / `wait` / `passed` |
| `half_life_hours` | float\|null | Hours until 50% of cascade done |
| `elapsed_pct` | float\|null | % of cascade already played out |
| `time_to_90pct_hours` | float\|null | Hours until 90% complete — practical exit signal |
| `decay_rate` | string | `fast` (<2h) / `moderate` (2–8h) / `slow` (>8h) / `unknown` |

**Example response:**
```json
{
  "updated_at": "2026-04-10T13:03:01Z",
  "data_age_minutes": 8.2,
  "universe_size": 80,
  "signals_found": 34,
  "signals": [
    {
      "symbol": "GITLAWB",
      "score": 0.531,
      "rank": 1,
      "signal_type": "spike",
      "ais": 0.208,
      "velocity": 7.06,
      "att_pct": 18.78,
      "ATT_delta_1h": "-1.4pp",
      "cascade_multiplier": 2.17,
      "half_life_hours": 6.7,
      "organic_fraction": 0.351,
      "divergence_detected": false,
      "spike_history": null,
      "key_factors": ["high velocity 7.1×"],
      "caution": ["thin_spike_history"],
      "timing": {
        "window_open": true,
        "entry_quality": "strong",
        "urgency": "act_now",
        "half_life_hours": 6.7,
        "elapsed_pct": 19.8,
        "time_to_90pct_hours": 22.2,
        "decay_rate": "moderate"
      },
      "signal_interpretation": {
        "propagation_mode": "organic",
        "followthrough": "uncertain",
        "decay_risk": "low",
        "flow_type": "mixed",
        "price_alignment": "roughly_aligned",
        "summary": "building",
        "agent_action_hint": "monitor"
      }
    }
  ]
}
```

---

## GET /v1/token/{symbol} — $0.45

Full deep dive on one token. Everything in one call: attention, live price, hawkes, timing, narrative, spike history.

**Params:**

| Param | Values | Default |
|---|---|---|
| `?hours=` | 1–168 | 4 — lookback for recent_posts and narrative |

**Response structure:**

| Field | Type | Description |
|---|---|---|
| `symbol` | string | Token symbol |
| `updated_at` | string | Last data update |
| `window_hours` | int | Requested lookback window |
| `attention.ATT_pct` | float | Composite attention share (%) |
| `attention.MS_pct` | float | Mindshare (%) |
| `attention.INF_pct` | float | Influence (%) |
| `attention.velocity` | float | Momentum multiplier vs 48h baseline |
| `attention.mentions_2h` | int | Raw mentions in last 2h |
| `attention.engagement_quality` | float | Fraction of posts with ≥10 likes |
| `attention.top_account` | object | `{ username, followers }` — top posting account |
| `attention.ATT_trend_direction` | string | `building` / `stable` / `reversing` |
| `attention.ATT_accelerating` | bool | true = rate of attention growth is itself accelerating |
| `ATT_delta_1h` | string | Attention change last 1h (e.g. "+3.2pp") |
| `ATT_delta_4h` | string | Attention change last 4h |
| `price.price_usd` | float | Live price from GeckoTerminal |
| `price.change_1h_pct` | float | 1h price change (%) |
| `price.change_24h_pct` | float | 24h price change (%) |
| `price.market_cap` | float\|null | Market cap USD |
| `price.volume_24h` | float\|null | 24h volume USD |
| `price.liquidity` | float\|null | Pool liquidity USD |
| `price.fetched_at` | string | When price was fetched (always live) |
| `divergence.detected` | bool | true = attention up, price flat/down |
| `divergence.note` | string\|null | Human-readable divergence description |
| `spike_history.confirmed` | int | Historical spikes with confirmed price follow-through |
| `spike_history.total` | int | Total historical spikes detected |
| `spike_history.hit_rate` | float\|null | confirmed / total. null if <5 total |
| `timing` | object | Full timing block (see below) |
| `narrative.summary` | string\|null | AI-generated 180-char brief |
| `narrative.signal_type` | string | Signal type of most recent narrative |
| `narrative.detected_at` | string | When the spike was detected |
| `narrative.price_at_post` | float\|null | Price when narrative was posted |
| `recent_posts[]` | array | Top posts ≥10 likes: `{ text, author, likes, retweets, created_at }` |
| `hawkes` | object | Full Hawkes intelligence block (see below) |

**Full timing block (in /v1/token):**

| Field | Type | Description |
|---|---|---|
| `window_open` | bool | Is this still worth entering? |
| `entry_quality` | string | `strong` / `moderate` / `weak` / `closed` |
| `urgency` | string | `act_now` / `monitor` / `wait` / `passed` |
| `peak_attention_in_hours` | float\|null | Estimated hours until attention peaks. null if already past |
| `half_life_hours` | float\|null | Hours until 50% of cascade done |
| `time_to_90pct_hours` | float\|null | Hours until 90% complete — practical exit signal |
| `cascade_multiplier` | float | Expected total wave size |
| `expected_mentions_remaining` | float\|null | Model estimate of mentions before decay |
| `elapsed_pct` | float\|null | % of cascade already played out |
| `decay_rate` | string | `fast` (<2h) / `moderate` (2–8h) / `slow` (>8h) / `unknown` |
| `decay_alpha` | float\|null | Raw exponential decay rate |
| `viral_class` | string | `BUILDING` / `LIKELY_VIRAL` / `SUSTAINED` / `LIKELY_FADING` / `UNCERTAIN` |
| `acceleration` | float | Hawkes acceleration score |
| `organic_fraction` | float | Community-driven share (0–1) |
| `elapsed_hours_since_analysis` | float\|null | Hours since Hawkes model was last fitted |
| `caution` | array | Timing-specific flags |
| `data_quality` | string | `complete` / `partial` / `stale` / `insufficient_data` |

**Hawkes block fields:**

| Field | Type | Description |
|---|---|---|
| `ais` | float | Attention Intelligence Score (0–1) |
| `ais_confidence` | string | `HIGH` / `MEDIUM` / `LOW` |
| `signal` | string | Hawkes signal label |
| `regime` | string | `BUILDING` / `SUSTAINED` / `SPIKE_AND_FADE` / `NOISE` |
| `viral_class` | string | Virality classification |
| `branching_factor` | float | Expected replies per post. >0.8 = self-sustaining cascade |
| `branching_factor_weighted` | float | Follower-weighted branching. Higher gap vs branching_factor = influential accounts amplifying |
| `cascade_multiplier` | float | Expected total wave size. Entry sizing signal |
| `viral_potential` | float | SEISMIC score (p_hat). >2.0 = high viral potential |
| `decay_alpha` | float\|null | Exponential decay rate. Low = lingers. High = fades fast |
| `half_life_hours` | float\|null | Hours until 50% of cascade plays out |
| `acceleration` | float | Rate of acceleration in posting activity |
| `organic_fraction` | float | Community-driven share (f_endo). >0.5 = self-reinforcing |
| `influence_concentration` | float | 0 = distributed. 1 = single whale. High = fragile signal |
| `market_share` | float | Token's share of total Hawkes market |
| `competition_pressure` | float | Competitive pressure from other tokens (0–1) |
| `top_competitors` | array | `[{ symbol, pressure }]` — tokens competing for same creator attention |
| `analyzed_at` | string | When Hawkes model was last fitted |
| `hawkes_status` | string | `complete` / `partial` / `stale` / `insufficient_data` |
| `signal_interpretation` | object | 7-field agent block |

---

## GET /v1/rotation — $0.10

Directed creator rotation graph — which accounts moved between tokens, with ATT growth confirmation.

**Params:**

| Param | Values | Default |
|---|---|---|
| `?window=` | 1h \| 4h | 4h |
| `?limit=` | 1–25 | 10 |
| `?confirmed_only=` | bool | true — only tokens where creator inflow converted to ATT growth |

**Response fields:**

| Field | Type | Description |
|---|---|---|
| `edges[].from` | string | Token losing creator attention |
| `edges[].to` | string | Token gaining creator attention |
| `edges[].weight` | int | Number of creators who moved |
| `edges[].top_creator.username` | string | Most influential creator who moved |
| `edges[].top_creator.followers` | int | Follower count |
| `edges[].top_creator.max_likes` | int | Max likes on their posts in window |
| `nodes[].symbol` | string | Token symbol |
| `nodes[].inflow` | int | Creator accounts entering |
| `nodes[].outflow` | int | Creator accounts leaving |
| `nodes[].net_flow` | int | inflow − outflow |
| `nodes[].post_count` | int | Total posts in window |
| `nodes[].ATT_growth` | float\|null | ATT% change during window (%) |
| `nodes[].signal_interpretation` | object | 7-field agent block |

**Example response:**
```json
{
  "window": "4h",
  "data_age_minutes": 8.2,
  "edges": [
    {
      "from": "ROBOTMONEY",
      "to": "GITLAWB",
      "weight": 3,
      "top_creator": {
        "username": "@00Q__",
        "followers": 136531,
        "max_likes": 82
      }
    }
  ],
  "nodes": [
    {
      "symbol": "GITLAWB",
      "inflow": 3,
      "outflow": 0,
      "post_count": 11,
      "net_flow": 3,
      "ATT_growth": 22.0,
      "signal_interpretation": {
        "propagation_mode": "organic",
        "followthrough": "uncertain",
        "decay_risk": "low",
        "flow_type": "mixed",
        "price_alignment": "roughly_aligned",
        "summary": "building",
        "agent_action_hint": "monitor"
      }
    }
  ]
}
```

---

## GET /v1/bankr — $0.05

Bankr agent universe attention dashboard — competitive intelligence for the bankr ecosystem.

**Params:**

| Param | Values | Default |
|---|---|---|
| `?hours=` | 1–24 | 4 |
| `?sort_by=` | ATT_pct \| ATT_delta \| velocity | ATT_pct |

**Response fields:**

| Field | Type | Description |
|---|---|---|
| `leaderboard[].symbol` | string | Agent token symbol |
| `leaderboard[].ATT_pct` | float | Attention share normalized within bankr universe (%) |
| `leaderboard[].ATT_base` | float | Raw attention share in full Base ecosystem (%) |
| `leaderboard[].ATT_delta` | float | Change in ATT_base vs prior window (pp) |
| `leaderboard[].velocity` | float | Momentum multiplier vs baseline |
| `leaderboard[].mentions` | int | Mentions in window |
| `leaderboard[].unique_authors` | int | Distinct posting accounts |
| `leaderboard[].rank` | int | Position within bankr universe |
| `leaderboard[].fee_revenue_24h` | float\|null | 24h fee revenue USD (GeckoTerminal) |
| `leaderboard[].signal_interpretation` | object | 7-field agent block |
| `total_attention_share` | float | Combined Base ecosystem ATT% for all bankr agents |

**Example response:**
```json
{
  "updated_at": "2026-04-10T13:03:01Z",
  "data_age_minutes": 0.0,
  "window_hours": 4,
  "total_attention_share": 22.4,
  "leaderboard": [
    {
      "symbol": "gitlawb",
      "ATT_pct": 44.6,
      "ATT_base": 12.4,
      "ATT_delta": 0.3,
      "velocity": 4.2,
      "mentions": 11,
      "unique_authors": 11,
      "rank": 1,
      "fee_revenue_24h": 312.50,
      "signal_interpretation": {
        "propagation_mode": "organic",
        "followthrough": "uncertain",
        "decay_risk": "low",
        "flow_type": "mixed",
        "price_alignment": "roughly_aligned",
        "summary": "building",
        "agent_action_hint": "monitor"
      }
    }
  ]
}
```

---

## signal_interpretation — Field Reference

Every token entry on every endpoint includes a `signal_interpretation` block. This is the same translation the checkr.social dashboard renders as trader cards, but structured for agents to parse directly.

```json
"signal_interpretation": {
  "propagation_mode": "quiet | organic | viral",
  "followthrough":    "strong | thin | uncertain",
  "decay_risk":       "imminent | pending | low | unknown",
  "flow_type":        "organic | exogenous | mixed",
  "price_alignment":  "aligned | misaligned | roughly_aligned | unknown",
  "summary":          "rotation_risk | early_momentum | fading_spike | sustained_build | exogenous_event | noise | building",
  "agent_action_hint":"high_conviction | flag | monitor | deprioritize | rotate_out"
}
```

**`propagation_mode`** — how the conversation is spreading

| Value | Meaning |
|---|---|
| `quiet` | Mostly external triggers, low community echo (f_endo < 0.3) |
| `organic` | Community self-amplification (f_endo 0.3–0.6) |
| `viral` | Self-sustaining cascade, high branching (f_endo > 0.6 or n > 0.8) |

**`followthrough`** — will this attention sustain?

| Value | Meaning |
|---|---|
| `strong` | Branching high, regime building — will compound |
| `thin` | Branching low or fading — won't compound, window closing |
| `uncertain` | Not enough data |

**`decay_risk`** — how fast will attention collapse?

| Value | Meaning |
|---|---|
| `imminent` | Half-life < 1h or already fading — act now or skip |
| `pending` | 1–4h window before decay |
| `low` | Sustained or building — durable signal |
| `unknown` | No decay data |

**`flow_type`** — where is attention coming from?

| Value | Meaning |
|---|---|
| `organic` | Community-driven (f_endo > 0.5) |
| `exogenous` | External events driving it (f_endo < 0.35) |
| `mixed` | Both sources |

**`price_alignment`** — does this attention type historically move price?

| Value | Meaning |
|---|---|
| `aligned` | Organic flow + high AIS — historically precedes price |
| `misaligned` | Exogenous + weak AIS — likely won't convert |
| `roughly_aligned` | Mixed signals |
| `unknown` | Insufficient data |

**`agent_action_hint`** — the key field for downstream agents

| Value | Recommended action |
|---|---|
| `high_conviction` | Strong organic build — worth full deep-dive and position sizing |
| `flag` | Notable signal — track closely |
| `monitor` | Watch but don't act yet |
| `deprioritize` | Fading or noise — move attention elsewhere |
| `rotate_out` | Attention leaving this token |

---

## Caution Flags Reference

Caution flags appear in `signals[].caution` (signal endpoint) and `timing.caution` (token endpoint):

| Flag | Meaning |
|---|---|
| `half_life_under_1h` | Narrative fades in <1h — extremely time-sensitive |
| `high_influence_concentration` | One whale driving most activity — fragile signal |
| `high_competition_pressure` | Strong competing tokens pulling creator attention |
| `exogenous_heavy` | External catalyst driving it — less likely to compound organically |
| `thin_spike_history` | <5 historical spikes — hit_rate unavailable |
| `stale_hawkes_data` | Hawkes model not refreshed recently |
| `partial_hawkes_data` | Some Hawkes fields unavailable |
| `well_past_half_life` | Elapsed time >> half-life — cascade mostly done |
