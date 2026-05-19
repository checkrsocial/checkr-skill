"""
Enhanced social_context with dev/founder prioritization.

Fetches from BOTH cashtag queries AND dev_queries, prioritizing
official team voices in feed summary.
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

WORKSPACE = Path(__file__).parent.parent.parent


def _get_posts_all_sources(symbol: str, hours: int = 48, limit: int = 50) -> list:
    """
    Fetch posts from ALL queries for this symbol:
    1. Cashtag query (base movers cashtag $SYMBOL)
    2. Dev query (dev_queries for official team)
    
    Prioritize dev posts, then community.
    Returns all posts sorted by: dev_first, then engagement.
    """
    try:
        from attention import x_db
        con = x_db.connect()
        x_db.init_schema(con)

        all_posts = []

        # 1. Fetch from cashtag query
        cashtag_rows = con.execute(
            "SELECT id FROM x_queries WHERE enabled=1 AND name LIKE ? ORDER BY id ASC LIMIT 1",
            (f"base movers cashtag {symbol}%",)
        ).fetchall()
        
        # 2. Fetch from dev query (if exists)
        dev_rows = con.execute(
            "SELECT id FROM x_queries WHERE enabled=1 AND name LIKE ? ORDER BY id ASC LIMIT 1",
            (f"dev_queries {symbol}%",)
        ).fetchall()

        start = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

        # Get cashtag posts
        if cashtag_rows:
            qid = cashtag_rows[0][0]
            posts_rows = con.execute(
                """SELECT text, author_json, metrics_json, created_at, 'cashtag' as source
                   FROM x_posts
                   WHERE query_id=? AND created_at > ? AND (is_spam IS NULL OR is_spam=0)
                   ORDER BY created_at DESC LIMIT ?""",
                (qid, start, limit)
            ).fetchall()
            
            for row in posts_rows:
                all_posts.append(_parse_post_row(row, is_dev=False))

        # Get dev posts (prioritize these)
        if dev_rows:
            qid = dev_rows[0][0]
            posts_rows = con.execute(
                """SELECT text, author_json, metrics_json, created_at, 'dev' as source
                   FROM x_posts
                   WHERE query_id=? AND created_at > ? AND (is_spam IS NULL OR is_spam=0)
                   ORDER BY created_at DESC LIMIT ?""",
                (qid, start, limit)
            ).fetchall()
            
            for row in posts_rows:
                all_posts.append(_parse_post_row(row, is_dev=True))

        con.close()

        # Sort: dev first, then by engagement (likes)
        all_posts.sort(key=lambda p: (-p["is_dev"], -p["likes"]))
        
        return all_posts[:limit]

    except Exception as e:
        print(f"Error fetching posts: {e}")
        return []


def _parse_post_row(row, is_dev: bool) -> dict:
    """Parse a post row from database."""
    try:
        text, author_json, metrics_json, created_at, source = row
        metrics = json.loads(metrics_json or "{}")
        author = json.loads(author_json or "{}")
        likes = metrics.get("like_count", 0)
        
        username = author.get("userName") or author.get("username", "")
        followers = author.get("followers", 0)

        # Tier
        if followers >= 50000:
            tier = "macro"
        elif followers >= 10000:
            tier = "micro"
        else:
            tier = "nano"

        return {
            "text": text,
            "author": f"@{username}" if username else None,
            "followers": followers,
            "tier": tier,
            "likes": likes,
            "retweets": metrics.get("retweet_count", 0),
            "created_at": created_at,
            "source": source,  # 'cashtag' or 'dev'
            "is_dev": is_dev,  # dev query posts rank higher
        }
    except Exception:
        return None


def extract_dev_first_themes(posts: list) -> dict:
    """
    Extract themes with priority to dev/founder posts.
    
    Separates posts into:
    - Dev posts (from dev_queries)
    - Community posts (from cashtag query)
    """
    if not posts:
        return None

    dev_posts = [p for p in posts if p.get("is_dev")]
    community_posts = [p for p in posts if not p.get("is_dev")]

    themes = {
        "dev_narrative": None,      # What team is saying
        "community_narrative": None, # What community is saying
        "combined": {               # Both together
            "product": [],
            "ecosystem": [],
            "fundamentals": [],
            "sentiment": [],
            "other": []
        }
    }

    # Keywords for theme detection
    product_keywords = ["ship", "launch", "release", "deploy", "feature", "update", "live", "beta", "v2", "v3", "fix", "improve"]
    ecosystem_keywords = ["partner", "integrat", "cross-chain", "base", "chain", "protocol", "agent", "framework"]
    fundamental_keywords = ["revenue", "tvl", "apy", "apr", "metric", "growth", "traction", "user", "transaction", "volume"]
    bullish_keywords = ["bullish", "opportunity", "undervalue", "moon", "gem", "building", "real", "thesis", "strong", "moat"]
    bearish_keywords = ["bearish", "overvalue", "dump", "fud", "concern", "risk", "worry"]

    # Process dev posts
    if dev_posts:
        dev_themes = {"product": [], "ecosystem": [], "fundamentals": [], "other": []}
        for post in dev_posts:
            text = post["text"].lower()
            if any(kw in text for kw in product_keywords):
                dev_themes["product"].append(post)
            elif any(kw in text for kw in ecosystem_keywords):
                dev_themes["ecosystem"].append(post)
            elif any(kw in text for kw in fundamental_keywords):
                dev_themes["fundamentals"].append(post)
            else:
                dev_themes["other"].append(post)
        
        # Build dev narrative from most prominent theme
        if dev_themes["product"]:
            themes["dev_narrative"] = {
                "theme": "Product Development",
                "posts": dev_themes["product"],
                "summary": f"Team announced {len(dev_themes['product'])} product updates"
            }
        elif dev_themes["ecosystem"]:
            themes["dev_narrative"] = {
                "theme": "Ecosystem Activity",
                "posts": dev_themes["ecosystem"],
                "summary": f"Team working on {len(dev_themes['ecosystem'])} ecosystem developments"
            }
        elif dev_themes["fundamentals"]:
            themes["dev_narrative"] = {
                "theme": "Metrics & Fundamentals",
                "posts": dev_themes["fundamentals"],
                "summary": f"Team sharing {len(dev_themes['fundamentals'])} fundamental updates"
            }

    # Process community posts
    if community_posts:
        community_themes = {"product": [], "ecosystem": [], "fundamentals": [], "sentiment": [], "other": []}
        for post in community_posts:
            text = post["text"].lower()
            if any(kw in text for kw in product_keywords):
                community_themes["product"].append(post)
            elif any(kw in text for kw in ecosystem_keywords):
                community_themes["ecosystem"].append(post)
            elif any(kw in text for kw in fundamental_keywords):
                community_themes["fundamentals"].append(post)
            elif any(kw in text for kw in bullish_keywords):
                community_themes["sentiment"].append((post, "bullish"))
            elif any(kw in text for kw in bearish_keywords):
                community_themes["sentiment"].append((post, "bearish"))
            else:
                community_themes["other"].append(post)
        
        # Build community narrative
        if community_themes["product"]:
            themes["community_narrative"] = {
                "theme": "Product Discussion",
                "posts": community_themes["product"],
                "summary": f"Community discussing {len(community_themes['product'])} product aspects"
            }
        elif community_themes["ecosystem"]:
            themes["community_narrative"] = {
                "theme": "Ecosystem Narrative",
                "posts": community_themes["ecosystem"],
                "summary": f"Community highlighting {len(community_themes['ecosystem'])} ecosystem points"
            }

    return themes


def build_dev_first_feed_summary(symbol: str, hours: int = 48) -> dict:
    """
    Build feed summary with dev posts prioritized.
    
    Returns:
    - dev_posts: What the team is saying
    - community_posts: What the community is saying
    - combined_summary: Overall narrative
    - sentiment: Overall sentiment
    """
    posts = _get_posts_all_sources(symbol, hours=hours, limit=50)
    
    if not posts:
        return {
            "summary": f"No recent posts found for {symbol} in last {hours}h.",
            "dev_posts": [],
            "community_posts": [],
            "dev_narrative": None,
            "combined_narrative": None,
            "sentiment": "unknown",
            "post_count": 0,
        }

    dev_posts = [p for p in posts if p.get("is_dev")]
    community_posts = [p for p in posts if not p.get("is_dev")]

    themes = extract_dev_first_themes(posts)

    # Build summary
    summary_parts = []
    if dev_posts:
        summary_parts.append(f"Team posted {len(dev_posts)} updates")
    if community_posts:
        summary_parts.append(f"Community discussing ({len(community_posts)} posts)")
    
    if dev_posts and themes.get("dev_narrative"):
        summary_parts.append(f"on {themes['dev_narrative']['theme']}")
    
    summary = " • ".join(summary_parts) if summary_parts else f"Feed discussing {symbol}"

    # Sentiment analysis
    bullish_posts = len([p for p in posts if any(kw in p["text"].lower() for kw in ["bullish", "opportunity", "gem", "moon"])])
    bearish_posts = len([p for p in posts if any(kw in p["text"].lower() for kw in ["bearish", "risk", "fud", "concern"])])
    
    if bullish_posts > bearish_posts:
        sentiment = "bullish"
    elif bearish_posts > bullish_posts:
        sentiment = "bearish"
    elif bullish_posts > 0 or bearish_posts > 0:
        sentiment = "mixed"
    else:
        sentiment = "neutral"

    return {
        "summary": summary,
        "dev_posts": [
            {
                "author": p["author"],
                "followers": p["followers"],
                "text": p["text"],
                "likes": p["likes"],
                "created_at": p["created_at"],
            }
            for p in dev_posts[:5]  # Top 5 dev posts
        ],
        "dev_narrative": themes.get("dev_narrative") if themes else None,
        "community_posts": [
            {
                "author": p["author"],
                "followers": p["followers"],
                "text": p["text"],
                "likes": p["likes"],
                "created_at": p["created_at"],
            }
            for p in community_posts[:5]  # Top 5 community posts
        ],
        "community_narrative": themes.get("community_narrative") if themes else None,
        "combined_summary": summary,
        "sentiment": sentiment,
        "post_count": len(posts),
        "dev_post_count": len(dev_posts),
        "community_post_count": len(community_posts),
        "posts_by_tier": {
            "macro": len([p for p in posts if p["tier"] == "macro"]),
            "micro": len([p for p in posts if p["tier"] == "micro"]),
            "nano": len([p for p in posts if p["tier"] == "nano"]),
        },
    }
