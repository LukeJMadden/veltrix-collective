"""
Scout — Agent 1 for Veltrix Collective
Monitors RSS feeds, Reddit, and Hacker News for AI news.
Scores each item with Claude and saves qualifying items to Supabase.
Runs every 3 hours via GitHub Actions.
"""

import os
import sys
import json
import time
import hashlib
import logging
import requests
import feedparser
from datetime import datetime, timezone, timedelta
from dateutil import parser as dateparser
import anthropic
from supabase import create_client

# ── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("scout")

# ── Config ───────────────────────────────────────────────────────────────────

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]

LOOKBACK_HOURS = 4          # Fetch items from the last N hours (buffer for cron drift)
SCORE_THRESHOLD = 65        # Min Claude relevance score to save (0–100)
MAX_ITEMS_PER_RUN = 30      # Cap to control API costs
HN_STORIES_TO_CHECK = 100   # How many top HN new stories to evaluate

# RSS feeds to monitor
RSS_FEEDS = [
    {"name": "TechCrunch AI",    "url": "https://techcrunch.com/category/artificial-intelligence/feed/"},
    {"name": "The Verge AI",     "url": "https://www.theverge.com/ai-artificial-intelligence/rss/index.xml"},
    {"name": "Anthropic Blog",   "url": "https://www.anthropic.com/news/rss.xml"},
    {"name": "OpenAI Blog",      "url": "https://openai.com/blog/rss.xml"},
    {"name": "Hugging Face",     "url": "https://huggingface.co/blog/feed.xml"},
    {"name": "MIT Tech Review",  "url": "https://www.technologyreview.com/feed/"},
    {"name": "VentureBeat AI",   "url": "https://venturebeat.com/category/ai/feed/"},
]

# Reddit subreddits to monitor
SUBREDDITS = [
    "artificial",
    "MachineLearning",
    "ClaudeAI",
    "ChatGPT",
    "singularity",
    "LLMDevs",
]

# ── Supabase client ───────────────────────────────────────────────────────────

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
claude   = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

# ── Helpers ───────────────────────────────────────────────────────────────────

def url_hash(url: str) -> str:
    """Stable 12-char fingerprint for dedup."""
    return hashlib.sha256(url.encode()).hexdigest()[:12]


def already_saved(url: str) -> bool:
    """Check if this URL is already in the news table."""
    h = url_hash(url)
    result = supabase.table("news").select("id").eq("url_hash", h).limit(1).execute()
    return bool(result.data)


def parse_date(date_str) -> datetime | None:
    """Parse a date string into a UTC-aware datetime, or return None."""
    if not date_str:
        return None
    try:
        dt = dateparser.parse(str(date_str))
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


def is_recent(dt: datetime | None, hours: int = LOOKBACK_HOURS) -> bool:
    """True if dt is within the lookback window."""
    if dt is None:
        return True  # If we can't parse the date, include it to be safe
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    return dt >= cutoff


# ── Fetch functions ───────────────────────────────────────────────────────────

def fetch_rss() -> list[dict]:
    items = []
    for feed_cfg in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_cfg["url"])
            for entry in feed.entries:
                pub = parse_date(entry.get("published") or entry.get("updated"))
                if not is_recent(pub):
                    continue
                items.append({
                    "source": feed_cfg["name"],
                    "title": entry.get("title", "").strip(),
                    "url": entry.get("link", "").strip(),
                    "summary_raw": entry.get("summary", "")[:500],
                    "published_at": pub,
                })
            log.info(f"RSS [{feed_cfg['name']}] → {len(feed.entries)} entries checked")
        except Exception as e:
            log.warning(f"RSS fetch failed [{feed_cfg['name']}]: {e}")
    return items


def fetch_reddit() -> list[dict]:
    items = []
    headers = {"User-Agent": "VeltrixScout/1.0 (news aggregator)"}
    cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
    for sub in SUBREDDITS:
        try:
            url = f"https://www.reddit.com/r/{sub}/new.json?limit=25"
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            posts = resp.json()["data"]["children"]
            for post in posts:
                p = post["data"]
                created = datetime.fromtimestamp(p["created_utc"], tz=timezone.utc)
                if created < cutoff:
                    continue
                # Skip self-posts with no external link, low-effort posts
                if p.get("is_self") and p.get("score", 0) < 20:
                    continue
                link = p.get("url") or f"https://reddit.com{p.get('permalink','')}"
                items.append({
                    "source": f"r/{sub}",
                    "title": p.get("title", "").strip(),
                    "url": link,
                    "summary_raw": p.get("selftext", "")[:300],
                    "published_at": created,
                    "score_raw": p.get("score", 0),
                })
            log.info(f"Reddit [r/{sub}] → {len(posts)} posts checked")
            time.sleep(0.5)  # Polite rate limit
        except Exception as e:
            log.warning(f"Reddit fetch failed [r/{sub}]: {e}")
    return items


def fetch_hackernews() -> list[dict]:
    items = []
    try:
        ids = requests.get(
            "https://hacker-news.firebaseio.com/v0/newstories.json",
            timeout=10
        ).json()[:HN_STORIES_TO_CHECK]

        cutoff = datetime.now(timezone.utc) - timedelta(hours=LOOKBACK_HOURS)
        for story_id in ids:
            try:
                story = requests.get(
                    f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json",
                    timeout=8
                ).json()
                if not story or story.get("type") != "story":
                    continue
                created = datetime.fromtimestamp(story.get("time", 0), tz=timezone.utc)
                if created < cutoff:
                    continue
                url = story.get("url")
                if not url:
                    url = f"https://news.ycombinator.com/item?id={story_id}"
                items.append({
                    "source": "Hacker News",
                    "title": story.get("title", "").strip(),
                    "url": url,
                    "summary_raw": "",
                    "published_at": created,
                    "score_raw": story.get("score", 0),
                })
                time.sleep(0.05)
            except Exception:
                continue
        log.info(f"HN → {len(items)} recent stories found")
    except Exception as e:
        log.warning(f"HN fetch failed: {e}")
    return items


# ── Claude scoring & summarisation ───────────────────────────────────────────

SCORE_PROMPT = """You are a relevance filter for Veltrix Collective, an AI tools and news site.

Score the following article for relevance to our audience: people who use, build with, or follow AI tools, LLMs, and AI automation.

HIGH relevance (75–100): New AI tools, LLM releases, benchmark results, AI automation news, Claude/GPT/Gemini updates, AI business news, prompt engineering, developer AI tools.
MEDIUM relevance (50–74): AI research with practical implications, big-tech AI strategy, AI regulation news.
LOW relevance (0–49): Pure academic papers, unrelated tech, vague AI opinion pieces, cryptocurrency, gaming.

Title: {title}
Source: {source}
Preview: {preview}

Respond with ONLY a JSON object, no other text:
{{"score": <0-100>, "reason": "<10 words max>"}}"""

SUMMARY_PROMPT = """You are Veltix, the AI persona behind Veltrix Collective (veltrixcollective.com).

Write a 3-sentence summary of this article in Veltix's voice: authoritative, slightly irreverent, never corporate. First person plural ("we", "our"). Specific about what matters and why. No filler phrases.

Article title: {title}
Source: {source}
Preview: {preview}

Write ONLY the 3-sentence summary. No intro, no quotes around it."""


def score_item(item: dict) -> int:
    """Ask Claude to score relevance. Returns 0 on failure."""
    try:
        msg = claude.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=80,
            messages=[{
                "role": "user",
                "content": SCORE_PROMPT.format(
                    title=item["title"],
                    source=item["source"],
                    preview=item.get("summary_raw", "")[:200],
                )
            }]
        )
        raw = msg.content[0].text.strip()
        data = json.loads(raw)
        score = int(data.get("score", 0))
        log.info(f"  Score {score:3d} | {item['title'][:60]} [{data.get('reason','')}]")
        return score
    except Exception as e:
        log.warning(f"  Score failed: {e} | {item['title'][:50]}")
        return 0


def summarise_item(item: dict) -> str:
    """Generate a Veltix-voice summary. Returns empty string on failure."""
    try:
        msg = claude.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": SUMMARY_PROMPT.format(
                    title=item["title"],
                    source=item["source"],
                    preview=item.get("summary_raw", "")[:300],
                )
            }]
        )
        return msg.content[0].text.strip()
    except Exception as e:
        log.warning(f"  Summarise failed: {e}")
        return ""


# ── Supabase write ────────────────────────────────────────────────────────────

def save_item(item: dict, score: int, summary: str) -> bool:
    """Insert a news item into Supabase. Returns True on success."""
    try:
        pub_str = item["published_at"].isoformat() if item.get("published_at") else datetime.now(timezone.utc).isoformat()
        supabase.table("news").insert({
            "headline":     item["title"],
            "summary":      summary,
            "source_url":   item["url"],
            "url_hash":     url_hash(item["url"]),
            "source_name":  item["source"],
            "relevance_score": score,
            "published_at": pub_str,
        }).execute()
        return True
    except Exception as e:
        log.error(f"  Save failed: {e} | {item['title'][:50]}")
        return False


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("Scout starting")
    log.info(f"Lookback window: {LOOKBACK_HOURS}h | Score threshold: {SCORE_THRESHOLD}")
    log.info("=" * 60)

    # 1. Collect all candidate items
    all_items = []
    all_items.extend(fetch_rss())
    all_items.extend(fetch_reddit())
    all_items.extend(fetch_hackernews())

    log.info(f"\nTotal candidates: {len(all_items)}")

    # 2. Deduplicate by URL
    seen_urls = set()
    unique_items = []
    for item in all_items:
        if not item.get("url") or not item.get("title"):
            continue
        url = item["url"].strip()
        if url in seen_urls:
            continue
        seen_urls.add(url)
        unique_items.append(item)

    log.info(f"After dedup: {len(unique_items)}")

    # 3. Filter already-saved items
    new_items = [i for i in unique_items if not already_saved(i["url"])]
    log.info(f"Not yet in DB: {len(new_items)}")

    # 4. Cap to avoid excessive API calls
    if len(new_items) > MAX_ITEMS_PER_RUN:
        log.info(f"Capping to {MAX_ITEMS_PER_RUN} items")
        new_items = new_items[:MAX_ITEMS_PER_RUN]

    # 5. Score, summarise, save
    saved = 0
    skipped = 0
    for item in new_items:
        score = score_item(item)
        if score < SCORE_THRESHOLD:
            skipped += 1
            continue
        summary = summarise_item(item)
        if save_item(item, score, summary):
            saved += 1

    log.info("\n" + "=" * 60)
    log.info(f"Scout complete — saved: {saved} | skipped (low score): {skipped}")
    log.info("=" * 60)

    # Exit with error if nothing was saved and there were candidates (helps spot feed issues)
    if saved == 0 and len(new_items) > 5:
        log.warning("No items saved despite candidates — check feeds or threshold")


if __name__ == "__main__":
    main()
