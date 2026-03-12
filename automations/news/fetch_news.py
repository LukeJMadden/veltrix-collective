#!/usr/bin/env python3
"""
fetch_news.py — Veltrix News Pipeline
Runs hourly. Fetches AI news from RSS feeds, filters new items,
summarises each in Veltrix voice, and saves to Supabase.
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import feedparser
from datetime import datetime, timezone, timedelta
from utils.common import get_logger, get_supabase, get_anthropic, log_run, VELTRIX_SYSTEM_PROMPT, slugify

logger = get_logger("fetch_news")

RSS_FEEDS = [
    {"url": "https://techcrunch.com/category/artificial-intelligence/feed/", "source": "TechCrunch"},
    {"url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "source": "The Verge"},
    {"url": "https://www.anthropic.com/news/rss.xml", "source": "Anthropic"},
    {"url": "https://openai.com/news/rss.xml", "source": "OpenAI"},
    {"url": "https://huggingface.co/blog/feed.xml", "source": "Hugging Face"},
    {"url": "https://venturebeat.com/category/ai/feed/", "source": "VentureBeat"},
    {"url": "https://arstechnica.com/ai/feed/", "source": "Ars Technica"},
]

def fetch_feed(feed_info: dict) -> list[dict]:
    """Fetch and parse a single RSS feed."""
    try:
        feed = feedparser.parse(feed_info["url"])
        items = []
        cutoff = datetime.now(timezone.utc) - timedelta(hours=3)
        for entry in feed.entries[:20]:
            published = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
            else:
                published = datetime.now(timezone.utc)

            if published < cutoff:
                continue

            items.append({
                "headline": entry.get("title", ""),
                "source_url": entry.get("link", ""),
                "source_name": feed_info["source"],
                "published_at": published.isoformat(),
                "raw_summary": entry.get("summary", entry.get("description", ""))[:500],
            })
        logger.info(f"  {feed_info['source']}: {len(items)} new items")
        return items
    except Exception as e:
        logger.warning(f"  {feed_info['source']} feed failed: {e}")
        return []

def is_duplicate(supabase, source_url: str) -> bool:
    """Check if this URL is already in the DB."""
    res = supabase.table("news").select("id").eq("source_url", source_url).execute()
    return len(res.data) > 0

def summarise_item(client, item: dict) -> str:
    """Generate a Veltrix-voice 3-sentence summary."""
    try:
        msg = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=200,
            system=VELTRIX_SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": f"""Write a 2-3 sentence summary of this AI news item in Veltrix voice.
Be direct and factual. No hype. No filler.

Headline: {item['headline']}
Source: {item['source_name']}
Raw content: {item['raw_summary']}

Return ONLY the summary sentences. No intro, no quotes around it."""
            }]
        )
        return msg.content[0].text.strip()
    except Exception as e:
        logger.warning(f"Summarise failed: {e}")
        return item["raw_summary"][:280] if item["raw_summary"] else item["headline"]

def main():
    logger.info("=== Veltrix News Fetch Starting ===")
    supabase = get_supabase()
    client = get_anthropic()

    all_items = []
    for feed in RSS_FEEDS:
        items = fetch_feed(feed)
        all_items.extend(items)

    logger.info(f"Total candidates: {len(all_items)}")

    saved = 0
    for item in all_items:
        if not item["headline"] or not item["source_url"]:
            continue
        if is_duplicate(supabase, item["source_url"]):
            continue

        # Summarise
        summary = summarise_item(client, item)

        # Save to DB
        try:
            supabase.table("news").insert({
                "headline": item["headline"][:500],
                "summary": summary,
                "source_url": item["source_url"],
                "source_name": item["source_name"],
                "published_at": item["published_at"],
            }).execute()
            saved += 1
            logger.info(f"  Saved: {item['headline'][:60]}...")
        except Exception as e:
            logger.warning(f"  DB insert failed: {e}")

    logger.info(f"Saved {saved} new items.")
    log_run(supabase, "fetch_news", "success", f"Saved {saved} new items", saved)

if __name__ == "__main__":
    main()
