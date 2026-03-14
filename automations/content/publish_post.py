"""
Publisher - Agent 3 for Veltrix Collective
Runs after Writer. Finds the oldest unpublished draft, flips it to published,
generates social captions in Veltix voice, saves to social_posts table,
and posts to X and LinkedIn if API keys are present.
Triggered daily at 3am UTC via GitHub Actions (1h after Writer).
"""

import os, re, logging
from datetime import datetime, timezone
import openai, anthropic
from supabase import create_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("publisher")

SUPABASE_URL  = os.environ["SUPABASE_URL"]
SUPABASE_KEY  = os.environ["SUPABASE_SERVICE_KEY"]
OPENAI_KEY    = os.environ["OPENAI_API_KEY"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
SITE_URL      = "https://veltrixcollective.com"

# Social keys - optional. Script skips gracefully if not set.
X_API_KEY            = os.environ.get("X_API_KEY", "")
X_API_SECRET         = os.environ.get("X_API_SECRET", "")
X_ACCESS_TOKEN       = os.environ.get("X_ACCESS_TOKEN", "")
X_ACCESS_SECRET      = os.environ.get("X_ACCESS_SECRET", "")
LINKEDIN_ACCESS_TOKEN = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
LINKEDIN_PERSON_URN  = os.environ.get("LINKEDIN_PERSON_URN", "")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def call_ai(prompt, max_tokens=500, quality=False):
    openai_model    = "gpt-4o"            if quality else "gpt-4o-mini"
    anthropic_model = "claude-sonnet-4-6" if quality else "claude-haiku-4-5-20251001"
    try:
        client = openai.OpenAI(api_key=OPENAI_KEY)
        resp = client.chat.completions.create(
            model=openai_model, max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        log.warning(f"OpenAI failed ({e}), falling back to Anthropic")
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        msg = client.messages.create(
            model=anthropic_model, max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text.strip()


# ── Fetch oldest unpublished draft ───────────────────────────────────────
def fetch_draft():
    result = (
        supabase.table("posts")
        .select("id, title, slug, excerpt, category, tags, content")
        .eq("status", "draft")
        .order("created_at", desc=False)
        .limit(1)
        .execute()
    )
    return result.data[0] if result.data else None


# ── Publish post ─────────────────────────────────────────────────────────
def publish_post(post_id):
    now = datetime.now(timezone.utc).isoformat()
    supabase.table("posts").update({
        "status": "published",
        "published_at": now,
        "updated_at": now,
    }).eq("id", post_id).execute()
    log.info(f"  Published post ID {post_id}")


# ── Generate social captions ──────────────────────────────────────────────
TWITTER_PROMPT = """You are Veltix from Veltrix Collective.
Write a single tweet (max 260 chars) about this post. Punchy, specific, no hype.
End with this URL: {url}

Post title: {title}
Excerpt: {excerpt}

Return ONLY the tweet text. No quotes around it."""

LINKEDIN_PROMPT = """You are Veltix from Veltrix Collective.
Write a LinkedIn post (150-250 words) about this article. Authoritative and insightful.
First line is a hook. Use short paragraphs. End with a CTA linking to: {url}

Post title: {title}
Excerpt: {excerpt}

Return ONLY the LinkedIn post text. No quotes around it."""


def generate_social_captions(post):
    url = f"{SITE_URL}/blog/{post['slug']}"
    twitter = call_ai(TWITTER_PROMPT.format(
        url=url, title=post["title"], excerpt=post.get("excerpt", "")[:200]
    ), max_tokens=120)
    linkedin = call_ai(LINKEDIN_PROMPT.format(
        url=url, title=post["title"], excerpt=post.get("excerpt", "")[:200]
    ), max_tokens=400)
    log.info(f"  Twitter ({len(twitter)} chars): {twitter[:60]}...")
    log.info(f"  LinkedIn ({len(linkedin)} chars)")
    return twitter, linkedin


# ── Save social posts to DB ───────────────────────────────────────────────
def save_social_post(post_id, platform, content, platform_post_id=""):
    supabase.table("social_posts").insert({
        "post_id":          post_id,
        "platform":         platform,
        "content":          content,
        "status":           "published" if platform_post_id else "draft",
        "platform_post_id": platform_post_id,
    }).execute()


# ── Post to X (Twitter) ───────────────────────────────────────────────────
def post_to_x(text, post_id):
    if not all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET]):
        log.info("  X keys not set — saving caption as draft")
        save_social_post(post_id, "twitter", text)
        return
    try:
        import tweepy
        client = tweepy.Client(
            consumer_key=X_API_KEY, consumer_secret=X_API_SECRET,
            access_token=X_ACCESS_TOKEN, access_token_secret=X_ACCESS_SECRET
        )
        resp = client.create_tweet(text=text)
        tweet_id = str(resp.data["id"])
        save_social_post(post_id, "twitter", text, tweet_id)
        log.info(f"  Posted to X: tweet ID {tweet_id}")
    except Exception as e:
        log.warning(f"  X post failed: {e} — saving as draft")
        save_social_post(post_id, "twitter", text)


# ── Post to LinkedIn ─────────────────────────────────────────────────────
def post_to_linkedin(text, post_id, post_url):
    if not all([LINKEDIN_ACCESS_TOKEN, LINKEDIN_PERSON_URN]):
        log.info("  LinkedIn keys not set — saving caption as draft")
        save_social_post(post_id, "linkedin", text)
        return
    try:
        import requests
        payload = {
            "author": f"urn:li:person:{LINKEDIN_PERSON_URN}",
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text},
                    "shareMediaCategory": "ARTICLE",
                    "media": [{"status": "READY", "originalUrl": post_url}]
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
        }
        r = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            json=payload,
            headers={"Authorization": f"Bearer {LINKEDIN_ACCESS_TOKEN}", "Content-Type": "application/json"},
            timeout=15
        )
        r.raise_for_status()
        li_id = r.json().get("id", "")
        save_social_post(post_id, "linkedin", text, li_id)
        log.info(f"  Posted to LinkedIn: {li_id}")
    except Exception as e:
        log.warning(f"  LinkedIn post failed: {e} — saving as draft")
        save_social_post(post_id, "linkedin", text)


# ── Log run ───────────────────────────────────────────────────────────────
def log_run(status, message, records=0):
    try:
        supabase.table("automation_logs").insert({
            "script_name": "publisher", "status": status,
            "message": message, "records_processed": records,
        }).execute()
    except Exception as e:
        log.warning(f"Automation log failed: {e}")


# ── Main ─────────────────────────────────────────────────────────────────
def main():
    log.info("=" * 60)
    log.info("Publisher starting")
    log.info("=" * 60)

    post = fetch_draft()
    if not post:
        msg = "No draft posts to publish"
        log.info(msg)
        log_run("skipped", msg)
        return

    log.info(f"Publishing: {post['title']}")
    publish_post(post["id"])

    post_url = f"{SITE_URL}/blog/{post['slug']}"
    log.info(f"  Live at: {post_url}")

    log.info("Generating social captions...")
    twitter_text, linkedin_text = generate_social_captions(post)

    log.info("Posting to social platforms...")
    post_to_x(twitter_text, post["id"])
    post_to_linkedin(linkedin_text, post["id"], post_url)

    log_run("success", f"Published: {post['title'][:80]}", 1)
    log.info("=" * 60)
    log.info(f"Publisher complete — {post['title'][:60]}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()