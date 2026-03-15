"""
Agent 2: Writer
---------------
Picks the top unwritten news story (relevance_score >= 75, no post_id yet, last 48h)
and writes a full SEO blog post in Veltix voice. Saves to posts table as published.
Runs daily at 2am UTC via GitHub Actions.
"""

import os, re, json, logging
from datetime import datetime, timezone
import openai
import anthropic
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ── Env ──────────────────────────────────────────────────────────────────────
SUPABASE_URL  = os.environ["SUPABASE_URL"]
SUPABASE_KEY  = os.environ["SUPABASE_SERVICE_KEY"]
OPENAI_KEY    = os.environ["OPENAI_API_KEY"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}

# ── AI call ───────────────────────────────────────────────────────────────────
def call_ai(prompt: str, max_tokens: int = 2000, quality: bool = True) -> str:
    openai_model    = "gpt-4o"            if quality else "gpt-4o-mini"
    anthropic_model = "claude-sonnet-4-6" if quality else "claude-haiku-4-5-20251001"
    try:
        client = openai.OpenAI(api_key=OPENAI_KEY)
        resp = client.chat.completions.create(
            model=openai_model, max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content
    except Exception as e:
        log.warning(f"OpenAI failed ({e}), falling back to Anthropic")
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        msg = client.messages.create(
            model=anthropic_model, max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text

# ── Supabase helpers ──────────────────────────────────────────────────────────
def get_top_story() -> dict | None:
    """Fetch the highest-scoring unused news item from the last 48h."""
    url = (
        f"{SUPABASE_URL}/rest/v1/news"
        f"?select=id,headline,summary,source_url,source_name,category,relevance_score"
        f"&relevance_score=gte.75"
        f"&post_id=is.null"
        f"&published_at=gte.{_hours_ago(48)}"
        f"&order=relevance_score.desc"
        f"&limit=1"
    )
    r = requests.get(url, headers=HEADERS)
    r.raise_for_status()
    data = r.json()
    return data[0] if data else None


def save_post(post: dict) -> int:
    """Insert post into Supabase, return the new post ID."""
    url = f"{SUPABASE_URL}/rest/v1/posts"
    r = requests.post(url, headers=HEADERS, json=post)
    r.raise_for_status()
    return r.json()[0]["id"]


def mark_news_used(news_id: int, post_id: int):
    url = f"{SUPABASE_URL}/rest/v1/news?id=eq.{news_id}"
    r = requests.patch(url, headers=HEADERS, json={"post_id": post_id})
    r.raise_for_status()


def _hours_ago(h: int) -> str:
    from datetime import timedelta
    dt = datetime.now(timezone.utc) - timedelta(hours=h)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

# ── Slug helper ───────────────────────────────────────────────────────────────
def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text[:80]


def unique_slug(base: str) -> str:
    slug = slugify(base)
    # append timestamp suffix to guarantee uniqueness
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    return f"{slug}-{ts}"

# ── Writing prompt ────────────────────────────────────────────────────────────
WRITE_PROMPT = """
You are Veltix, the AI persona behind Veltrix Collective (veltrixcollective.com).

Voice: Authoritative but approachable. First person plural — "we track", "we tested", "our rankings".
Tone: Slightly irreverent. Never corporate. Never hype. Specific about what matters.
Avoid: Excessive exclamation marks. Vague statements. "In today's fast-paced world". Claiming to be human or Claude.
Always end with a CTA to a Veltrix tool or the insider paywall at veltrixcollective.com.

Weave in naturally (don't force it): "you need AI to keep up with AI"

---

Write a full blog post based on this news item:

Headline: {headline}
Summary: {summary}
Source: {source_name} ({source_url})
Category: {category}

Return ONLY valid JSON (no markdown fences, no preamble) with these exact keys:
{{
  "title": "Engaging post title (not just the headline)",
  "slug_base": "3-6 word slug-friendly title",
  "excerpt": "2-sentence plain-text excerpt for preview cards",
  "content": "Full HTML blog post body. Use <h2>, <p>, <ul>, <li>, <strong> tags. Minimum 600 words. Include at least 3 sections. End with a CTA paragraph.",
  "category": "one of: ai-news | analysis | tools | tutorials",
  "tags": ["tag1", "tag2", "tag3"],
  "meta_title": "SEO title under 60 chars",
  "meta_description": "SEO description 120-155 chars"
}}
"""

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    log.info("Writer agent starting")

    story = get_top_story()
    if not story:
        log.info("No eligible stories found. Exiting.")
        return

    log.info(f"Writing post from news id={story['id']}: {story['headline'][:80]}")

    prompt = WRITE_PROMPT.format(
        headline=story["headline"],
        summary=story["summary"],
        source_name=story["source_name"],
        source_url=story["source_url"],
        category=story["category"],
    )

    raw = call_ai(prompt, max_tokens=3000, quality=True)

    # Strip accidental markdown fences
    raw = re.sub(r"^```json\s*", "", raw.strip())
    raw = re.sub(r"```$", "", raw.strip())

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        log.error(f"Failed to parse AI JSON: {e}\nRaw:\n{raw[:500]}")
        raise

    now = datetime.now(timezone.utc).isoformat()
    post = {
        "title":            data["title"],
        "slug":             unique_slug(data.get("slug_base", data["title"])),
        "content":          data["content"],
        "excerpt":          data["excerpt"],
        "status":           "published",
        "category":         data["category"],
        "tags":             data.get("tags", []),
        "meta_title":       data["meta_title"],
        "meta_description": data["meta_description"],
        "is_paywalled":     False,
        "published_at":     now,
        "updated_at":       now,
    }

    post_id = save_post(post)
    mark_news_used(story["id"], post_id)

    log.info(f"✅ Post saved: id={post_id} slug={post['slug']}")
    log.info(f"   Title: {post['title']}")


if __name__ == "__main__":
    main()
