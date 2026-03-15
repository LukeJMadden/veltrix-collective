#!/usr/bin/env python3
"""
Agent 3: Publisher
Runs daily at 5am UTC via GitHub Actions (after Writer at 2am).
Finds the most recent published post, generates a 3-tweet thread,
posts to Twitter (@Veltrix_C) via Composio, logs to social_posts table.
"""

import os
import json
import logging
from datetime import datetime, timezone

import openai
import anthropic
import requests
from composio import Composio, Action

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

SUPABASE_URL   = os.environ["SUPABASE_URL"]
SUPABASE_KEY   = os.environ["SUPABASE_SERVICE_KEY"]
OPENAI_KEY     = os.environ["OPENAI_API_KEY"]
ANTHROPIC_KEY  = os.environ["ANTHROPIC_API_KEY"]
COMPOSIO_KEY   = os.environ["COMPOSIO_API_KEY"]
SITE_URL       = "https://veltrixcollective.com"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

BRAND_VOICE = """
You are Veltix, the AI persona behind Veltrix Collective (veltrixcollective.com).
Voice: Authoritative but approachable. Direct. Specific. Never corporate, never hype.
Twitter style: Short, punchy, no fluff. Use numbers and specifics where possible.
"""


def call_ai(prompt: str, max_tokens: int = 800) -> str:
    try:
        client = openai.OpenAI(api_key=OPENAI_KEY)
        resp = client.chat.completions.create(
            model="gpt-4o",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content
    except Exception as e:
        log.warning(f"OpenAI failed ({e}), falling back to Anthropic")
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text


def get_latest_post() -> dict | None:
    """Get the most recent published post that hasn't been tweeted yet."""
    # Get posts not in social_posts with platform=twitter
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/posts",
        headers=HEADERS,
        params={
            "select": "id,title,excerpt,slug",
            "status": "eq.published",
            "order": "published_at.desc",
            "limit": "10",
        }
    )
    resp.raise_for_status()
    posts = resp.json()

    if not posts:
        return None

    # Find first post not already tweeted
    for post in posts:
        check = requests.get(
            f"{SUPABASE_URL}/rest/v1/social_posts",
            headers=HEADERS,
            params={
                "post_id": f"eq.{post['id']}",
                "platform": "eq.twitter",
                "status": "eq.published",
            }
        )
        if not check.json():
            return post

    log.info("All recent posts already tweeted.")
    return None


def generate_thread(post: dict) -> list[str]:
    """Generate a 3-tweet thread for a post."""
    post_url = f"{SITE_URL}/blog/{post['slug']}"

    prompt = f"""{BRAND_VOICE}

Create a 3-tweet thread for this AI news post. Rules:
- Tweet 1: Hook only. No link. Max 240 chars. Grab attention with a specific fact or bold claim.
- Tweet 2: Core insight. The most important thing to understand. Include a specific number or stat if possible. Max 240 chars. No link.
- Tweet 3: Takeaway + CTA + the link: {post_url}. Max 240 chars.
- Each tweet stands alone but flows as a thread.
- No hashtags on tweet 1 or 2. 1-2 relevant hashtags on tweet 3 only.
- Do NOT use em dashes. Do NOT use quotes around the tweets.

Post title: {post['title']}
Post excerpt: {post['excerpt']}

Return ONLY a JSON array of exactly 3 strings. No markdown fences. No extra keys.
Example: ["Tweet 1 text", "Tweet 2 text", "Tweet 3 text with {post_url}"]"""

    raw = call_ai(prompt)
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    tweets = json.loads(raw)
    assert len(tweets) == 3, f"Expected 3 tweets, got {len(tweets)}"
    for t in tweets:
        assert len(t) <= 280, f"Tweet too long ({len(t)} chars): {t}"
    return tweets


def post_thread(tweets: list[str]) -> list[str]:
    """Post a 3-tweet thread via Composio. Returns list of tweet IDs."""
    composio = Composio(api_key=COMPOSIO_KEY)
    tweet_ids = []
    reply_to_id = None

    for i, text in enumerate(tweets):
        params = {"text": text}
        if reply_to_id:
            params["reply"] = {"in_reply_to_tweet_id": reply_to_id}

        result = composio.tools.execute(
            slug="TWITTER_CREATION_OF_A_POST",
            params=params,
            user_id="default",
        )

        if not result.get("successful", False):
            raise RuntimeError(f"Tweet {i+1} failed: {result.get('error', 'unknown error')}")

        tweet_id = result["data"]["data"]["id"]
        tweet_ids.append(tweet_id)
        reply_to_id = tweet_id
        log.info(f"Posted tweet {i+1}/{len(tweets)}: {tweet_id}")

    return tweet_ids


def log_to_supabase(post_id: int, tweets: list[str], tweet_ids: list[str]):
    """Log each tweet to social_posts table."""
    now = datetime.now(timezone.utc).isoformat()
    for tweet_text, tweet_id in zip(tweets, tweet_ids):
        requests.post(
            f"{SUPABASE_URL}/rest/v1/social_posts",
            headers=HEADERS,
            json={
                "post_id":          post_id,
                "platform":         "twitter",
                "content":          tweet_text,
                "status":           "published",
                "platform_post_id": tweet_id,
                "published_at":     now,
            }
        ).raise_for_status()
    log.info(f"Logged {len(tweets)} tweets to social_posts")


def main():
    log.info("Agent 3: Publisher starting")

    post = get_latest_post()
    if not post:
        log.info("No untweeted posts found. Exiting.")
        return

    log.info(f"Publishing post ID {post['id']}: {post['title']}")

    tweets = generate_thread(post)
    log.info(f"Thread generated:\n" + "\n---\n".join(tweets))

    tweet_ids = post_thread(tweets)
    log_to_supabase(post["id"], tweets, tweet_ids)

    log.info(f"Done. Thread live: https://x.com/Veltrix_C/status/{tweet_ids[0]}")


if __name__ == "__main__":
    main()
