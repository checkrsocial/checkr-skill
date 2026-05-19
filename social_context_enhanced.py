"""
Enhanced social_context with feed summary synthesis.

Adds narrative synthesis layer that reads actual tweets and builds
a cohesive summary of what's happening — not just links to posts,
but actual extracted details from the feed.
"""

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

WORKSPACE = Path(__file__).parent.parent.parent


def _get_posts_with_text(symbol: str, hours: int = 4, limit: int = 20) -> list:
    """Fetch recent posts with full text, ranked by engagement."""
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
               ORDER BY created_at DESC LIMIT ?""",
            (qid, start, limit)
        ).fetchall()
        con.close()

        posts = []
        for text, author_json, metrics_json, created_at in posts_rows:
            try:
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

                posts.append({
                    "text": text,
                    "author": f"@{username}" if username else None,
                    "followers": followers,
                    "tier": tier,
                    "likes": likes,
                    "retweets": metrics.get("retweet_count", 0),
                    "created_at": created_at,
                })
            except Exception:
                continue

        return posts

    except Exception:
        return []


def extract_feed_themes(posts: list) -> dict:
    """
    Analyze posts to extract recurring themes/topics.
    
    Groups posts by topic (product, ecosystem, fundamentals, sentiment, etc).
    Returns summary of what the feed is saying.
    """
    if not posts:
        return None

    themes = {
        "product": [],      # shipping, launch, features, update
        "ecosystem": [],    # partnerships, integrations, cross-chain
        "fundamentals": [], # metrics, revenue, TVL, utility
        "sentiment": [],    # bullish, bearish, narrative arguments
        "other": []
    }

    # Simple keyword matching
    product_keywords = ["ship", "launch", "release", "deploy", "feature", "update", "live", "beta", "v2", "v3", "beta", "fix", "improve"]
    ecosystem_keywords = ["partner", "integrat", "cross-chain", "base", "chain", "protocol", "agent", "framework"]
    fundamental_keywords = ["revenue", "tvl", "apy", "apr", "metric", "growth", "traction", "user", "transaction", "volume"]
    bullish_keywords = ["bullish", "opportunity", "undervalue", "moon", "gem", "building", "real", "thesis", "strong", "moat"]
    bearish_keywords = ["bearish", "overvalue", "dump", "fud", "concern", "risk", "worry"]

    for post in posts:
        text = post["text"].lower()
        categorized = False

        # Check categories (priority order)
        if any(kw in text for kw in product_keywords):
            themes["product"].append(post)
            categorized = True
        elif any(kw in text for kw in ecosystem_keywords):
            themes["ecosystem"].append(post)
            categorized = True
        elif any(kw in text for kw in fundamental_keywords):
            themes["fundamentals"].append(post)
            categorized = True
        
        # Sentiment is secondary
        if not categorized:
            if any(kw in text for kw in bullish_keywords):
                themes["sentiment"].append((post, "bullish"))
            elif any(kw in text for kw in bearish_keywords):
                themes["sentiment"].append((post, "bearish"))
            else:
                themes["other"].append(post)

    return themes


def build_feed_summary(symbol: str, hours: int = 4) -> dict:
    """
    Build a narrative summary of what the feed is actually saying.
    
    NOT just links to posts, but extracted details + context + direct quotes.
    """
    posts = _get_posts_with_text(symbol, hours=hours, limit=30)
    
    if not posts:
        return {
            "summary": "No recent posts found for this token in the last {} hours.".format(hours),
            "themes": [],
            "key_claims": [],
            "top_quotes": [],
            "sentiment": "unknown",
            "post_count": 0,
        }

    themes = extract_feed_themes(posts)

    # Build theme summaries
    theme_summaries = []

    if themes["product"]:
        top_posts = sorted(themes["product"], key=lambda p: p["likes"], reverse=True)[:2]
        claims = []
        for p in top_posts:
            # Extract what's being shipped/launched
            if "ship" in p["text"].lower() or "launch" in p["text"].lower():
                claims.append(p["text"][:100])
        if claims:
            theme_summaries.append({
                "theme": "Product Development",
                "evidence": claims,
                "posts_count": len(themes["product"]),
                "top_author": top_posts[0]["author"],
                "top_author_tier": top_posts[0]["tier"],
            })

    if themes["ecosystem"]:
        top_posts = sorted(themes["ecosystem"], key=lambda p: p["likes"], reverse=True)[:2]
        claims = []
        for p in top_posts:
            if any(kw in p["text"].lower() for kw in ["partner", "integrat", "launch"]):
                claims.append(p["text"][:100])
        if claims:
            theme_summaries.append({
                "theme": "Ecosystem Activity",
                "evidence": claims,
                "posts_count": len(themes["ecosystem"]),
                "top_author": top_posts[0]["author"],
                "top_author_tier": top_posts[0]["tier"],
            })

    if themes["fundamentals"]:
        top_posts = sorted(themes["fundamentals"], key=lambda p: p["likes"], reverse=True)[:2]
        metrics = []
        for p in top_posts:
            # Try to extract numbers
            import re
            numbers = re.findall(r'\$[\d.,]+[mMbBkK]?|\d+[%x×]', p["text"])
            if numbers:
                metrics.append(f"{p['author']}: {p['text'][:80]}")
        if metrics:
            theme_summaries.append({
                "theme": "Metrics & Fundamentals",
                "evidence": metrics,
                "posts_count": len(themes["fundamentals"]),
                "top_author": top_posts[0]["author"],
                "top_author_tier": top_posts[0]["tier"],
            })

    # Sentiment analysis
    bullish_posts = [p for p, s in themes["sentiment"] if s == "bullish"]
    bearish_posts = [p for p, s in themes["sentiment"] if s == "bearish"]
    
    if bullish_posts and not bearish_posts:
        dominant_sentiment = "bullish"
    elif bearish_posts and not bullish_posts:
        dominant_sentiment = "bearish"
    elif bullish_posts and bearish_posts:
        dominant_sentiment = "mixed"
    else:
        dominant_sentiment = "neutral"

    # Extract key claims (unique assertions)
    key_claims = []
    seen_claims = set()
    
    for post in sorted(posts, key=lambda p: p["likes"], reverse=True)[:10]:
        text = post["text"]
        # Look for sentences with claims (rough heuristic)
        if any(word in text.lower() for word in ["is", "are", "will", "has", "enables", "provides"]):
            claim = text[:90]
            if claim not in seen_claims:
                key_claims.append({
                    "claim": claim,
                    "from": post["author"],
                    "tier": post["tier"],
                    "engagement": post["likes"],
                })
                seen_claims.add(claim)

    key_claims = key_claims[:5]  # Top 5

    # Top quotes (highest engagement)
    top_quotes = sorted(posts, key=lambda p: p["likes"], reverse=True)[:5]

    # Build summary narrative
    if theme_summaries:
        summary_parts = [f"Feed organizing around {len(theme_summaries)} main themes:"]
        for ts in theme_summaries:
            summary_parts.append(f"• {ts['theme']}: {ts['posts_count']} posts")
        summary_text = " ".join(summary_parts)
    else:
        summary_text = f"Feed discussing ${symbol}. {len(posts)} posts in last {hours}h."

    return {
        "summary": summary_text,
        "themes": theme_summaries,
        "key_claims": key_claims,
        "top_quotes": [
            {
                "text": q["text"],
                "from": q["author"],
                "tier": q["tier"],
                "followers": q["followers"],
                "likes": q["likes"],
                "posted_at": q["created_at"],
            }
            for q in top_quotes
        ],
        "sentiment": dominant_sentiment,
        "post_count": len(posts),
        "posts_by_tier": {
            "macro": len([p for p in posts if p["tier"] == "macro"]),
            "micro": len([p for p in posts if p["tier"] == "micro"]),
            "nano": len([p for p in posts if p["tier"] == "nano"]),
        },
    }


def synthesize_narrative(symbol: str, hours: int = 4, max_length: int = 280) -> str:
    """
    Generate a SOUL.md-compliant narrative summary.
    
    Format: "$symbol + what happened + who's driving + narrative context"
    180-280 chars, lowercase, no emojis, no hype.
    """
    feed_data = build_feed_summary(symbol, hours=hours)
    
    if not feed_data["post_count"]:
        return f"${symbol.lower()} — no recent feed activity"

    # Build narrative from themes
    narrative_parts = [f"${symbol.lower()}"]

    # What's happening
    if feed_data["themes"]:
        main_theme = feed_data["themes"][0]
        narrative_parts.append(f"{main_theme['theme'].lower()}")

    # Who's driving it
    if feed_data["key_claims"]:
        top_claim = feed_data["key_claims"][0]
        narrative_parts.append(f"@{top_claim['from'].strip('@')}")

    # Sentiment
    if feed_data["sentiment"] in ("bullish", "bearish"):
        narrative_parts.append(f"{feed_data['sentiment']} framing")

    # Engagement
    narrative_parts.append(f"{feed_data['post_count']} posts, {feed_data['posts_by_tier']['macro']} macro voices")

    narrative = " — ".join(narrative_parts)

    # Trim to max_length
    if len(narrative) > max_length:
        narrative = narrative[:max_length-1] + "."

    return narrative
