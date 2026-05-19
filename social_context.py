"""
Social context layer for /v1/token/{symbol} endpoint.

Provides rich social narrative: what's happening on X right now, who's driving it,
what's the story, when did it start, will it last?

All data is pre-computed and cached. No real-time API calls.
"""

import json
import sqlite3
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

WORKSPACE = Path(__file__).parent.parent.parent
MOMENTUM_PATH = WORKSPACE / "attention" / "momentum.json"
HAWKES_PATH = WORKSPACE / "attention" / "hawkes_state.json"
PUBLISH_LOG_PATH = WORKSPACE / "attention" / "publish_log.json"


def _load_json(path: Path) -> dict:
    """Load JSON file with fallback."""
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return {}


def get_social_context_now(symbol: str) -> dict:
    """Current snapshot for the last 2 hours."""
    m = _load_json(MOMENTUM_PATH)
    current = m.get("current", {})
    vdata = current.get(symbol.upper(), {})

    if not vdata:
        return None

    # Get top account
    top_account_name = vdata.get("top_account_name", "")
    top_account_followers = vdata.get("top_account_followers", 0)

    # Tier classification
    if top_account_followers >= 50000:
        tier = "macro"
    elif top_account_followers >= 10000:
        tier = "micro"
    else:
        tier = "nano"

    return {
        "window": "2h",
        "mentions_count": vdata.get("mentions_2h", 0),
        "mentions_organic": vdata.get("organic_above_floor", 0),
        "unique_authors": vdata.get("U_authors", 0),
        "ATT_pct": round(vdata.get("ATT_pct", 0.0), 2),
        "velocity": round(vdata.get("velocity", 0.0), 2),
        "engagement_avg": round(vdata.get("engagement_baseline", 0.0), 1),
        "engagement_total": round(vdata.get("total_engagement_2h", 0.0), 0),
        "has_founder_post": vdata.get("has_founder_post", False),
        "top_account": {
            "username": f"@{top_account_name}" if top_account_name else None,
            "followers": top_account_followers,
            "tier": tier,
            "posts_in_window": vdata.get("top_account_posts_2h", 0),
            "top_post_likes": vdata.get("top_account_best_engagement", 0),
        } if top_account_name else None,
    }


def get_social_context_trend(symbol: str) -> dict:
    """Last 24h trend analysis."""
    m = _load_json(MOMENTUM_PATH)
    current = m.get("current", {})
    vdata = current.get(symbol.upper(), {})
    snapshots = m.get("snapshots_history", [])

    if not vdata:
        return None

    # Find 24h ago snapshot
    now_ts = datetime.now(timezone.utc)
    day_ago_ts = now_ts - timedelta(hours=24)

    att_24h_ago = None
    authors_24h_ago = None
    for snap in snapshots:
        snap_ts = datetime.fromisoformat(snap.get("timestamp", "").replace("Z", "+00:00"))
        if snap_ts < day_ago_ts:
            sym_snap = snap.get("current", {}).get(symbol.upper(), {})
            if sym_snap:
                att_24h_ago = sym_snap.get("ATT_pct")
                authors_24h_ago = sym_snap.get("U_authors")
                break

    att_now = vdata.get("ATT_pct", 0.0)
    authors_now = vdata.get("U_authors", 0)

    att_growth_pp = (att_now - (att_24h_ago or att_now)) if att_24h_ago else 0
    att_growth_pct = round((att_growth_pp / att_24h_ago * 100), 1) if att_24h_ago and att_24h_ago > 0 else 0

    # Direction
    if att_growth_pp > 0.5:
        direction = "accelerating"
    elif att_growth_pp < -0.5:
        direction = "fading"
    else:
        direction = "stable"

    # Authors trend
    authors_change = (authors_now - (authors_24h_ago or authors_now)) if authors_24h_ago else 0
    if authors_change > 0:
        authors_interpretation = "fresh author entry — cascade signature"
    elif authors_change < 0:
        authors_interpretation = "author pool shrinking — concentration risk"
    else:
        authors_interpretation = "stable author base"

    return {
        "direction": direction,
        "att_pct_24h_ago": round(att_24h_ago or att_now, 2),
        "att_pct_now": round(att_now, 2),
        "att_growth_pp": round(att_growth_pp, 2),
        "att_growth_pct": att_growth_pct,
        "mentions_24h": vdata.get("mentions_48h", 0),  # Approximation
        "mentions_peak_window": vdata.get("peak_window_label", "unknown"),
        "authors_trend": {
            "24h_ago": authors_24h_ago or authors_now,
            "now": authors_now,
            "net_change": authors_change,
            "interpretation": authors_interpretation,
        },
        "engagement_trend": {
            "avg_likes_peak": vdata.get("max_engagement_baseline", 0),
            "avg_likes_now": round(vdata.get("engagement_baseline", 0.0), 1),
            "quality_ratio": round(vdata.get("quality_ratio", 0.0), 3),
        },
    }


def get_social_context_timeline(symbol: str, hours: int = 72) -> dict:
    """3-day (or custom) hourly attention timeline."""
    m = _load_json(MOMENTUM_PATH)
    snapshots = m.get("snapshots_history", [])
    symbol_upper = symbol.upper()

    if not snapshots:
        return None

    # Build hourly data points
    now_ts = datetime.now(timezone.utc)
    start_ts = now_ts - timedelta(hours=hours)

    timeline_data = []
    for snap in snapshots:
        try:
            snap_ts = datetime.fromisoformat(snap.get("timestamp", "").replace("Z", "+00:00"))
            if snap_ts < start_ts:
                continue

            sym_snap = snap.get("current", {}).get(symbol_upper, {})
            if not sym_snap:
                continue

            timeline_data.append({
                "hour": snap_ts.isoformat(),
                "ATT_pct": round(sym_snap.get("ATT_pct", 0.0), 2),
                "mentions": sym_snap.get("mentions_2h", 0),
                "organic_posts": sym_snap.get("organic_above_floor", 0),
                "unique_authors": sym_snap.get("U_authors", 0),
                "velocity_vs_baseline": round(sym_snap.get("velocity", 0.0), 2),
                "regime": sym_snap.get("regime_label", "UNKNOWN"),
                "catalyst": sym_snap.get("last_catalyst_label", None),
            })
        except Exception:
            continue

    if not timeline_data:
        return None

    # Summarize trajectory
    formation_phase = timeline_data[0] if timeline_data else None
    acceleration_idx = None
    for i in range(1, len(timeline_data)):
        if timeline_data[i]["velocity_vs_baseline"] > 2.0 and \
           timeline_data[i-1]["velocity_vs_baseline"] <= 2.0:
            acceleration_idx = i
            break

    peak_point = max(timeline_data, key=lambda x: x["ATT_pct"]) if timeline_data else None

    # Trajectory classification
    if len(timeline_data) >= 2:
        recent = timeline_data[-1]["ATT_pct"]
        prior = timeline_data[-2]["ATT_pct"]
        if recent > prior * 1.1:
            trajectory = "building"
        elif recent < prior * 0.9:
            trajectory = "fading"
        else:
            trajectory = "sustained"
    else:
        trajectory = "unknown"

    h = _load_json(HAWKES_PATH)
    hawkes_for_symbol = h.get(symbol_upper, {})
    half_life = hawkes_for_symbol.get("half_life_hours", 6)

    return {
        "window": f"{hours}h",
        "granularity": "hourly",
        "data": timeline_data,
        "summary": {
            "formation_phase": formation_phase["hour"] if formation_phase else None,
            "acceleration_phase": timeline_data[acceleration_idx]["hour"] if acceleration_idx else None,
            "peak_attention": {
                "hour": peak_point["hour"] if peak_point else None,
                "ATT_pct": peak_point["ATT_pct"] if peak_point else None,
                "velocity": peak_point["velocity_vs_baseline"] if peak_point else None,
            } if peak_point else None,
            "half_life_estimated_hours": half_life,
            "trajectory": trajectory,
        },
    }


def get_social_context_narratives(symbol: str, hours: int = 4) -> dict:
    """Extract narratives from recent approved posts."""
    pub_log = _load_json(PUBLISH_LOG_PATH)
    posts = pub_log.get("posts", [])

    # Filter to recent posts for this symbol
    symbol_upper = symbol.upper()
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=hours)

    symbol_posts = []
    for p in posts:
        if p.get("coin", "").upper() != symbol_upper:
            continue
        try:
            post_ts = datetime.fromisoformat(p.get("posted_at", "").replace("Z", "+00:00"))
            if post_ts > start:
                symbol_posts.append(p)
        except Exception:
            continue

    if not symbol_posts:
        return {
            "primary_narrative": None,
            "secondary_narratives": [],
            "external_catalysts": [],
        }

    # Aggregate narratives
    primary_narrative = None
    if symbol_posts:
        latest = symbol_posts[0]  # Most recent post
        primary_narrative = {
            "theme": latest.get("signal_type", "unknown"),
            "description": latest.get("narrative", ""),
            "confidence": latest.get("confidence", 0.0),
            "timeline_started": latest.get("detected_at", latest.get("posted_at")),
            "account_diversity": len(set(p.get("narrative_author", "") for p in symbol_posts)),
            "organic_mentions": len(symbol_posts),
            "evidence": [
                {
                    "quote": p.get("narrative", ""),
                    "from": p.get("narrative_author", "unknown"),
                    "posted": p.get("posted_at"),
                    "likes": p.get("narrative_post_likes", 0),
                }
                for p in symbol_posts[:3]  # Top 3
            ],
        }

    return {
        "primary_narrative": primary_narrative,
        "secondary_narratives": [],  # TODO: extract from multiple posts
        "external_catalysts": [],    # TODO: from catalyst field in publish_log
    }


def get_social_context_top_accounts(symbol: str, hours: int = 4) -> list:
    """Rank accounts by influence on this symbol."""
    # Query x_db for posts and aggregate by author
    try:
        from attention import x_db
        con = x_db.connect()
        x_db.init_schema(con)

        rows = con.execute(
            "SELECT id FROM x_queries WHERE enabled=1 AND name LIKE ? ORDER BY id ASC LIMIT 1",
            (f"base movers cashtag {symbol}%",)
        ).fetchall()
        if not rows:
            con.close()
            return []

        qid = rows[0][0]
        start = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

        posts_rows = con.execute(
            """SELECT author_json, metrics_json, created_at, text
               FROM x_posts
               WHERE query_id=? AND created_at > ? AND (is_spam IS NULL OR is_spam=0)
               ORDER BY created_at DESC LIMIT 200""",
            (qid, start)
        ).fetchall()
        con.close()

        # Aggregate by author
        accounts = {}
        for author_json, metrics_json, created_at, text in posts_rows:
            try:
                metrics = json.loads(metrics_json or "{}")
                author = json.loads(author_json or "{}")
                likes = metrics.get("like_count", 0)
                if likes < 10:
                    continue

                username = author.get("userName") or author.get("username", "")
                followers = author.get("followers", 0)
                if username not in accounts:
                    accounts[username] = {
                        "username": f"@{username}",
                        "followers": followers,
                        "posts": [],
                        "total_likes": 0,
                    }

                accounts[username]["posts"].append({
                    "text": text,
                    "likes": likes,
                    "posted": created_at,
                })
                accounts[username]["total_likes"] += likes

            except Exception:
                continue

        # Rank by influence
        ranked = []
        for idx, (username, data) in enumerate(
            sorted(accounts.items(), key=lambda x: x[1]["total_likes"], reverse=True)[:10]
        ):
            followers = data["followers"]
            if followers >= 50000:
                tier = "macro"
            elif followers >= 10000:
                tier = "micro"
            else:
                tier = "nano"

            avg_likes = round(data["total_likes"] / len(data["posts"]), 1) if data["posts"] else 0
            influence_score = round((followers / 100000) * (avg_likes / 100), 2)  # Simple scoring

            ranked.append({
                "rank": idx + 1,
                "username": data["username"],
                "followers": followers,
                "tier": tier,
                "posts_24h": len(data["posts"]),
                "avg_likes_per_post": avg_likes,
                "engagement_influence_score": min(influence_score, 1.0),
                "recent_posts": data["posts"][:2],  # Top 2 posts
            })

        return ranked

    except Exception:
        return []


def _is_primary_subject(text: str, symbol: str) -> bool:
    """Check if the symbol is the primary subject, not just a co-mention.
    
    Rules:
    - If it's the FIRST cashtag → primary ✓
    - If it's in the first 100 chars → primary ✓
    - If it appears 3+ cashtags in → secondary ✗
    - Otherwise → edge cases treated as primary (benefit of doubt)
    """
    if not text:
        return False
    
    text_lower = text.lower()
    symbol_lower = f"${symbol.lower()}"
    
    import re
    cashtags = re.findall(r'\$[A-Za-z0-9]+', text, re.IGNORECASE)
    
    if not cashtags:
        return False
    
    # Rule 1: If this is the FIRST cashtag, it's primary
    if cashtags[0].lower() == symbol_lower:
        return True
    
    # Rule 2: If it appears in the first 100 chars, it's primary
    if symbol_lower in text_lower[:100]:
        return True
    
    # Rule 3: Count how many cashtags appear before it
    position_index = next((i for i, tag in enumerate(cashtags) if tag.lower() == symbol_lower), None)
    if position_index is not None and position_index >= 3:
        # If it's the 4th or later cashtag, it's a co-mention
        return False
    
    # Default: include it (benefit of doubt for edge cases)
    return True


def get_social_context_recent_posts(symbol: str, hours: int = 4) -> list:
    """Enhanced recent posts with impact scoring.
    
    Filters to posts where the symbol is the PRIMARY subject, not just a co-mention.
    """
    try:
        from attention import x_db
        con = x_db.connect()
        x_db.init_schema(con)

        rows = con.execute(
            "SELECT id FROM x_queries WHERE enabled=1 AND name LIKE ? ORDER BY id ASC LIMIT 1",
            (f"base movers cashtag {symbol}%",)
        ).fetchall()
        if not rows:
            con.close()
            return []

        qid = rows[0][0]
        start = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

        posts_rows = con.execute(
            """SELECT text, author_json, metrics_json, created_at
               FROM x_posts
               WHERE query_id=? AND created_at > ? AND (is_spam IS NULL OR is_spam=0)
               ORDER BY created_at DESC LIMIT 100""",  # Fetch more to filter
            (qid, start)
        ).fetchall()
        con.close()

        posts = []
        for text, author_json, metrics_json, created_at in posts_rows:
            try:
                # Filter: only include if symbol is primary subject
                if not _is_primary_subject(text, symbol):
                    continue
                
                metrics = json.loads(metrics_json or "{}")
                author = json.loads(author_json or "{}")
                likes = metrics.get("like_count", 0)
                if likes < 10:
                    continue

                username = author.get("userName") or author.get("username", "")
                followers = author.get("followers", 0)

                # Tier
                if followers >= 50000:
                    tier = "macro"
                elif followers >= 10000:
                    tier = "micro"
                else:
                    tier = "nano"

                # Impact score: engagement weighted by author tier
                base_score = min(likes / 500, 1.0)  # Normalize likes to 0-1
                tier_multiplier = {"macro": 1.5, "micro": 1.0, "nano": 0.5}[tier]
                impact_score = round(base_score * tier_multiplier, 2)

                posts.append({
                    "text": text,
                    "author": f"@{username}" if username else None,
                    "author_followers": followers,
                    "author_tier": tier,
                    "posted_at": created_at,
                    "likes": likes,
                    "retweets": metrics.get("retweet_count", 0),
                    "impact_score": impact_score,
                    "engagement_velocity": round(likes / 60, 1),  # Approx likes/hour
                })
            except Exception:
                continue

        # Sort by impact, return top 10
        posts.sort(key=lambda p: p["impact_score"], reverse=True)
        for idx, p in enumerate(posts[:10]):
            p["rank"] = idx + 1

        return posts[:10] if posts else []

    except Exception:
        return []


def get_social_context_momentum_signature(symbol: str) -> dict:
    """Hawkes signature translated to narrative."""
    h = _load_json(HAWKES_PATH)
    hawkes_data = h.get(symbol.upper(), {})

    if not hawkes_data:
        return None

    f_endo = hawkes_data.get("f_endo", 0.5)
    n = hawkes_data.get("n", 0.0)
    acceleration = hawkes_data.get("acceleration", 0.0)
    half_life = hawkes_data.get("half_life_hours", 6)

    # Propagation mode
    if n > 0.8 or f_endo > 0.6:
        propagation_mode = "viral"
    elif f_endo > 0.3:
        propagation_mode = "organic"
    else:
        propagation_mode = "exogenous"

    # Cascade strength
    if n > 0.7:
        cascade_strength = "strong"
    elif n > 0.3:
        cascade_strength = "moderate"
    else:
        cascade_strength = "weak"

    # Sustainability
    if propagation_mode == "organic" and n > 0.6:
        sustainability = "likely_sustained"
    elif half_life < 1.5:
        sustainability = "rapid_decay"
    elif propagation_mode == "exogenous":
        sustainability = "event_dependent"
    else:
        sustainability = "uncertain"

    interpretation = {
        ("organic", "strong"): "Self-sustaining community cascade. Each post inspires replies and new posts.",
        ("organic", "moderate"): "Community conversation building. Moderate self-reinforcement.",
        ("organic", "weak"): "Community interest, but slow feedback loop.",
        ("viral", "strong"): "Viral cascade — extreme self-reinforcement.",
        ("exogenous", "strong"): "External event driving intense (but temporary) attention.",
        ("exogenous", "moderate"): "External catalyst with some community response.",
        ("exogenous", "weak"): "Isolated external event, minimal organic follow-through.",
    }.get((propagation_mode, cascade_strength), "Unclear attention dynamics.")

    return {
        "propagation_mode": propagation_mode,
        "cascade_strength": cascade_strength,
        "f_endo": round(f_endo, 3),
        "branching_factor": round(n, 2),
        "acceleration": round(acceleration, 2),
        "interpretation": interpretation,
        "flow_health": {
            "is_self_reinforcing": n > 0.3,
            "concentration_risk": "high" if hawkes_data.get("influence_concentration", 0) > 0.6 else "moderate" if hawkes_data.get("influence_concentration", 0) > 0.4 else "low",
            "fatigue_risk": "high" if acceleration < 0.5 else "low",
            "sustainability": sustainability,
        },
        "half_life_hours": round(half_life, 1),
        "peak_likely_in_hours": round(half_life * 0.3, 1),  # Rough estimate: peak at 30% of half-life
    }


def build_social_context(symbol: str, hours: int = 4) -> dict:
    """Assemble complete social_context object."""
    # Import enhanced feed synthesis
    try:
        from attention.api import social_context_enhanced as sce
        feed_summary = sce.build_feed_summary(symbol, hours=hours)
    except Exception:
        feed_summary = None
    
    # Import dev-first feed synthesis (prioritizes dev/founder posts)
    try:
        from attention.api import social_context_with_dev as scd
        dev_first_summary = scd.build_dev_first_feed_summary(symbol, hours=48)
    except Exception:
        dev_first_summary = None
    
    return {
        "now": get_social_context_now(symbol),
        "trend": get_social_context_trend(symbol),
        "timeline": get_social_context_timeline(symbol, hours=72),
        "narratives": get_social_context_narratives(symbol, hours=hours),
        "top_accounts": get_social_context_top_accounts(symbol, hours=hours),
        "recent_posts": get_social_context_recent_posts(symbol, hours=hours),
        "momentum_signature": get_social_context_momentum_signature(symbol),
        "feed_summary": feed_summary,  # Basic feed synthesis
        "dev_context": dev_first_summary,  # NEW: Dev-prioritized feed (48h window)
    }
