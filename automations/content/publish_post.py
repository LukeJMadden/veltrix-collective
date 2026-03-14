"""
Publisher - Agent 3 for Veltrix Collective
Finds oldest draft post, publishes it, generates social captions,
posts to X if keys present, saves LinkedIn draft and emails it for manual review.
Triggered daily at 3am UTC via GitHub Actions (1h after Writer).
"""

import os, re, logging, requests
from datetime import datetime, timezone
import openai, anthropic
from supabase import create_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("publisher")

SUPABASE_URL  = os.environ["SUPABASE_URL"]
SUPABASE_KEY  = os.environ["SUPABASE_SERVICE_KEY"]
OPENAI_KEY    = os.environ["OPENAI_API_KEY"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
BREVO_KEY     = os.environ["BREVO_API_KEY"]
SITE_URL      = "https://veltrixcollective.com"
NOTIFY_EMAIL  = "hello@veltrixcollective.com"

# X keys - optional, posts live if present
X_API_KEY      = os.environ.get("X_API_KEY", "")
X_API_SECRET   = os.environ.get("X_API_SECRET", "")
X_ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN", "")
X_ACCESS_SECRET = os.environ.get("X_ACCESS_SECRET", "")

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


def publish_post(post_id):
    now = datetime.now(timezone.utc).isoformat()
    supabase.table("posts").update({
        "status": "published",
        "published_at": now,
        "updated_at": now,
    }).eq("id", post_id).execute()
    log.info(f"  Published post ID {post_id}")


# ── X (Twitter) caption ──────────────────────────────────────────────────
TWITTER_PROMPT = """You are Veltrix — the AI persona behind Veltrix Collective.
Write a single tweet (max 260 chars) about this post. Punchy, specific, no hype.
End with this URL: {url}

Post title: {title}
Excerpt: {excerpt}

Return ONLY the tweet text. No quotes."""


# ── LinkedIn caption (Luke's personal voice) ─────────────────────────────
# Luke is an AI practitioner and thought leader on AI + business.
# Voice: first-person, insightful, practitioner-level, never corporate.
# Veltrix mention: subtle and occasional — "been tracking this at veltrixcollective.com"
# style, not a direct ad. Omit Veltrix entirely in some posts.
LINKEDIN_PROMPT = """You are writing a LinkedIn post for Luke, an AI practitioner and
founder who shares genuine learnings about AI and its business impact.

Write a LinkedIn post (150-220 words) reacting to this AI news story.

Post title: {title}
Excerpt: {excerpt}
Article URL: {url}

Voice guidelines:
- First person singular (I, my, we when referring to work)
- Practitioner tone: share a real insight or implication, not just a summary
- Thought leadership: connect the news to a broader trend or business impact
- Hook first line — make it worth stopping the scroll
- Short paragraphs, 1-2 sentences each
- Never corporate-speak. Never "exciting times" or "game changer".
- {veltrix_mention}
- End with a question or a concrete takeaway that invites engagement

Return ONLY the LinkedIn post text. No intro, no quotes around it."""

import random

def get_veltrix_mention():
    """Rotate: 60% no mention, 25% subtle, 15% with link."""
    r = random.random()
    if r < 0.60:
        return "Do NOT mention Veltrix Collective or any project in this post."
    elif r < 0.85:
        return "Optionally weave in a subtle reference like 'been tracking this space closely' — no links, no project names."
    else:
        return f"You can naturally mention 'I've been tracking developments like this at veltrixcollective.com' once, only if it fits organically."


def generate_social_captions(post):
    url = f"{SITE_URL}/blog/{post['slug']}"
    twitter = call_ai(TWITTER_PROMPT.format(
        url=url, title=post["title"], excerpt=post.get("excerpt", "")[:200]
    ), max_tokens=120)
    linkedin = call_ai(LINKEDIN_PROMPT.format(
        url=url, title=post["title"],
        excerpt=post.get("excerpt", "")[:200],
        veltrix_mention=get_veltrix_mention()
    ), max_tokens=450)
    log.info(f"  Twitter ({len(twitter)} chars): {twitter[:60]}...")
    log.info(f"  LinkedIn ({len(linkedin)} chars)")
    return twitter, linkedin, url


def save_social_post(post_id, platform, content, platform_post_id=""):
    supabase.table("social_posts").insert({
        "post_id":          post_id,
        "platform":         platform,
        "content":          content,
        "status":           "published" if platform_post_id else "draft",
        "platform_post_id": platform_post_id,
    }).execute()


# ── Post to X ─────────────────────────────────────────────────────────────
def post_to_x(text, post_id):
    if not all([X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET]):
        log.info("  X keys not set — saving as draft")
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


# ── LinkedIn: save draft + email to Luke for manual posting ──────────────
def handle_linkedin(text, post_id, post_url, post_title):
    save_social_post(post_id, "linkedin", text)
    log.info("  LinkedIn caption saved as draft — sending email notification")
    send_linkedin_email(text, post_url, post_title)


def send_linkedin_email(caption, post_url, post_title):
    """Email the LinkedIn caption to Luke via Brevo for manual review + posting."""
    try:
        html = f"""
        <h2>LinkedIn post ready for review</h2>
        <p><strong>Article:</strong> <a href="{post_url}">{post_title}</a></p>
        <hr>
        <p style="white-space:pre-wrap;font-family:sans-serif;font-size:15px;line-height:1.6">{caption}</p>
        <hr>
        <p style="font-size:12px;color:#888">
        Copy the text above and post to <a href="https://linkedin.com">LinkedIn</a>.
        Edit freely — this is a draft in your voice.
        </p>
        """
        payload = {
            "sender":     {"name": "Veltrix Publisher", "email": "hello@veltrixcollective.com"},
            "to":         [{"email": NOTIFY_EMAIL}],
            "subject":    f"LinkedIn draft ready: {post_title[:60]}",
            "htmlContent": html,
        }
        r = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            json=payload,
            headers={"api-key": BREVO_KEY, "Content-Type": "application/json"},
            timeout=15
        )
        r.raise_for_status()
        log.info(f"  LinkedIn email sent to {NOTIFY_EMAIL}")
    except Exception as e:
        log.warning(f"  LinkedIn email failed: {e}")


def log_run(status, message, records=0):
    try:
        supabase.table("automation_logs").insert({
            "script_name": "publisher", "status": status,
            "message": message, "records_processed": records,
        }).execute()
    except Exception as e:
        log.warning(f"Automation log failed: {e}")


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
    twitter_text, linkedin_text, url = generate_social_captions(post)

    log.info("Posting to X...")
    post_to_x(twitter_text, post["id"])

    log.info("Handling LinkedIn (draft + email)...")
    handle_linkedin(linkedin_text, post["id"], url, post["title"])

    log_run("success", f"Published: {post['title'][:80]}", 1)
    log.info("=" * 60)
    log.info(f"Publisher complete — {post['title'][:60]}")
    log.info("=" * 60)


if __name__ == "__main__":
    main()