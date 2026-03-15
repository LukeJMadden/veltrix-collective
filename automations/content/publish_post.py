#!/usr/bin/env python3
"""
Agent 3: Publisher
Runs daily at 5am UTC via GitHub Actions.
Finds latest published post, generates 3-tweet thread,
posts to @Veltrix_C via Composio, logs to social_posts table.
"""

import os
import json
import logging
from datetime import datetime, timezone

import anthropic
import requests
from composio import Composio

try:
    import openai
    OPENAI_AVAILABLE = bool(os.environ.get("OPENAI_API_KEY"))
except ImportError:
    OPENAI_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

SUPABASE_URL  = os.environ["SUPABASE_URL"]
SUPABASE_KEY  = os.environ["SUPABASE_SERVICE_KEY"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
COMPOSIO_KEY  = os.environ["COMPOSIO_API_KEY"]
SITE_URL      = "https://veltrixcollective.com"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}


def call_ai(prompt: str, max_tokens: int = 800) -> str:
    if OPENAI_AVAILABLE:
        try:
            client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
            resp = client.chat.completions.create(
                model="gpt-4o", max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return resp.choices[0].message.content
        except Exception as e:
            log.warning(f"OpenAI failed ({e}), falling back to Anthropic")

    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    msg = client.messages.create(
        model="claude-sonnet-4-6", max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}]
    )
    return msg.content[0].text


def get_latest_post() -> dict | None:
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/posts",
        headers=HEADERS,
        params={"select": "id,title,excerpt,slug", "status": "eq.published",
                "order": "published_at.desc", "limit": "10"}
    )
    resp.raise_for_status()
    posts = resp.json()
    if not posts:
        return None

    for post in posts:
        check = requests.get(
            f"{SUPABASE_URL}/rest/v1/social_posts",
            headers=HEADERS,
            params={"post_id": f"eq.{post['id']}", "platform": "eq.twitter",
                    "status": "eq.published"}
        )
        if not check.json():
            return post

    log.info("All recent posts already tweeted.")
    return None


def generate_thread(post: dict) -> list[str]:
    post_url = f"{SITE_URL}/blog/{post['slug']}"
    prompt = f"""You are Veltix, AI persona behind Veltrix Collective.
Voice: Authoritative, direct, specific. Never hype. Never corporate.

Create a 3-tweet thread for this AI news post:
Title: {post['title']}
Excerpt: {post['excerpt']}

Rules:
- Tweet 1: Hook only. No link. Specific fact or bold claim. Max 240 chars.
- Tweet 2: Core insight with a number or stat if possible. No link. Max 240 chars.
- Tweet 3: Takeaway + CTA + link: {post_url}. 1-2 hashtags only on this tweet. Max 240 chars.
- No em dashes. No quotes around tweets.

Return ONLY a JSON array of exactly 3 strings. No markdown fences.
Example: ["Tweet 1", "Tweet 2", "Tweet 3"]"""

    raw = call_ai(prompt).strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()

    tweets = json.loads(raw)
    assert len(tweets) == 3, f"Expected 3 tweets, got {len(tweets)}"
    for t in tweets:
        assert len(t) <= 280, f"Tweet too long ({len(t)} chars): {t}"
    return tweets


def post_thread(tweets: list[str]) -> list[str]:
    """Post 3-tweet thread via Composio v0.11 SDK."""
    composio = Composio(api_key=COMPOSIO_KEY)
    tweet_ids = []
    reply_to_id = None

    for i, text in enumerate(tweets):
        # v0.11 uses `input` not `params`
        tool_input = {"text": text}
        if reply_to_id:
            tool_input["reply"] = {"in_reply_to_tweet_id": reply_to_id}

        result = composio.tools.execute(
            slug="TWITTER_CREATION_OF_A_POST",
            input=tool_input,
            user_id="default",
        )

        if not result.get("successful", False):
            raise RuntimeError(f"Tweet {i+1} failed: {result.get('error', result)}")

        tweet_id = result["data"]["data"]["id"]
        tweet_ids.append(tweet_id)
        reply_to_id = tweet_id
        log.info(f"Posted tweet {i+1}/3: id={tweet_id}")

    return tweet_ids


def log_to_supabase(post_id: int, tweets: list[str], tweet_ids: list[str]):
    now = datetime.now(timezone.utc).isoformat()
    for tweet_text, tweet_id in zip(tweets, tweet_ids):
        requests.post(
            f"{SUPABASE_URL}/rest/v1/social_posts",
            headers=HEADERS,
            json={"post_id": post_id, "platform": "twitter", "content": tweet_text,
                  "status": "published", "platform_post_id": tweet_id, "published_at": now}
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
    log.info("Thread generated:\n" + "\n---\n".join(tweets))

    tweet_ids = post_thread(tweets)
    log_to_supabase(post["id"], tweets, tweet_ids)

    log.info(f"Done. Thread live: https://x.com/Veltrix_C/status/{tweet_ids[0]}")


if __name__ == "__main__":
    main()
