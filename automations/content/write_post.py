#!/usr/bin/env python3
"""
Agent 2: Writer
Runs daily at 2am UTC via GitHub Actions.
Picks the top unwritten news story and writes a full SEO blog post in Veltix voice.
"""

import os
import re
import json
import logging
import hashlib
from datetime import datetime, timezone

import openai
import anthropic
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
OPENAI_KEY   = os.environ["OPENAI_API_KEY"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

BRAND_VOICE = """
You are Veltix, the AI persona behind Veltrix Collective (veltrixcollective.com).
Voice: Authoritative but approachable. First person plural. "we track", "we tested", "our rankings".
Tone: Slightly irreverent. Never corporate. Never hype. Specific about what matters.
Tagline: Occasionally weave in "you need AI to keep up with AI" naturally.
Avoid: Excessive exclamation marks. Vague statements. Claiming to be human or Claude.
Always end with a CTA to a Veltrix tool or the insider access page at veltrixcollective.com.
"""


def call_ai(prompt: str, max_tokens: int = 2000) -> str:
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


def get_top_story() -> dict | None:
    """Get the highest-scoring unwritten news story from the last 48 hours."""
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/news",
        headers=HEADERS,
        params={
            "select": "*",
            "post_id": "is.null",
            "relevance_score": "gte.75",
            "order": "relevance_score.desc",
            "limit": "1",
        }
    )
    resp.raise_for_status()
    items = resp.json()
    if not items:
        log.info("No unwritten stories with score >= 75 found.")
        return None
    return items[0]


def make_slug(title: str, post_id: int) -> str:
    base = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')[:60]
    suffix = hashlib.md5(str(post_id).encode()).hexdigest()[:6]
    return f"{base}-{suffix}"


def write_post(story: dict) -> dict:
    """Use AI to write a full blog post from a news story."""
    prompt = f"""{BRAND_VOICE}

Write a complete, SEO-optimised blog post about this AI news story.

STORY:
Headline: {story['headline']}
Summary: {story['summary']}
Source: {story['source_name']}
URL: {story['source_url']}

Return a JSON object with these exact keys:
- title: compelling SEO title (60 chars max)
- excerpt: 2-sentence summary for previews (150 chars max)
- content: full HTML blog post body (800-1200 words). Use <h2>, <p>, <ul>/<li> tags. No <html>/<body> wrapper.
- meta_title: SEO meta title (60 chars max)
- meta_description: SEO meta description (155 chars max)
- category: one of: ai-news, ai-tools, llm, productivity, industry
- tags: array of 3-5 relevant tags as strings

Return ONLY valid JSON. No markdown fences."""

    raw = call_ai(prompt, max_tokens=3000)
    # Strip any accidental markdown fences
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(raw)


def save_post(post_data: dict, story_id: int) -> int:
    """Save post to Supabase and return the new post ID."""
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "title":            post_data["title"],
        "excerpt":          post_data["excerpt"],
        "content":          post_data["content"],
        "meta_title":       post_data["meta_title"],
        "meta_description": post_data["meta_description"],
        "category":         post_data["category"],
        "tags":             post_data["tags"],
        "status":           "published",
        "published_at":     now,
        "is_paywalled":     False,
        "view_count":       0,
    }

    # Generate unique slug
    import random, string
    slug_base = re.sub(r'[^a-z0-9]+', '-', post_data["title"].lower()).strip('-')[:60]
    slug = f"{slug_base}-{random.choices(string.ascii_lowercase, k=6)}"
    payload["slug"] = slug

    resp = requests.post(
        f"{SUPABASE_URL}/rest/v1/posts",
        headers=HEADERS,
        json=payload
    )
    resp.raise_for_status()
    new_post = resp.json()[0]
    new_post_id = new_post["id"]

    # Mark news story as written
    requests.patch(
        f"{SUPABASE_URL}/rest/v1/news?id=eq.{story_id}",
        headers=HEADERS,
        json={"post_id": new_post_id}
    ).raise_for_status()

    log.info(f"Saved post ID {new_post_id}: {post_data['title']}")
    return new_post_id


def main():
    log.info("Agent 2: Writer starting")

    story = get_top_story()
    if not story:
        log.info("Nothing to write today. Exiting.")
        return

    log.info(f"Writing post for: {story['headline']} (score={story['relevance_score']})")

    post_data = write_post(story)
    post_id = save_post(post_data, story["id"])

    log.info(f"Done. Post ID: {post_id} | Title: {post_data['title']}")


if __name__ == "__main__":
    main()
