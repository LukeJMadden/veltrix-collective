"""
Writer - Agent 2 for Veltrix Collective
Pulls top-scoring news from Supabase, generates a full SEO blog post in Veltix
voice using OpenAI gpt-4o, saves as draft to posts table, logs the run.
Triggered daily at 2am UTC via GitHub Actions.
"""

import os, re, json, logging, hashlib
from datetime import datetime, timezone, timedelta
import openai, anthropic
from supabase import create_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("writer")

SUPABASE_URL  = os.environ["SUPABASE_URL"]
SUPABASE_KEY  = os.environ["SUPABASE_SERVICE_KEY"]
OPENAI_KEY    = os.environ["OPENAI_API_KEY"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]

NEWS_LOOKBACK_HOURS = 24
MIN_SCORE           = 70
MAX_CANDIDATES      = 10
TARGET_WORD_COUNT   = 900

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def call_ai(prompt, max_tokens=2000, quality=False):
    openai_model    = "gpt-4o"            if quality else "gpt-4o-mini"
    anthropic_model = "claude-sonnet-4-6" if quality else "claude-haiku-4-5-20251001"
    try:
        client = openai.OpenAI(api_key=OPENAI_KEY)
        resp = client.chat.completions.create(
            model=openai_model, max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        log.info(f"  AI [{openai_model}] responded")
        return resp.choices[0].message.content
    except Exception as e:
        log.warning(f"  OpenAI failed ({e}), falling back to Anthropic")
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        msg = client.messages.create(
            model=anthropic_model, max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text


def fetch_candidates():
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=NEWS_LOOKBACK_HOURS)).isoformat()
    result = (
        supabase.table("news")
        .select("id, headline, summary, source_url, source_name, relevance_score")
        .gte("relevance_score", MIN_SCORE)
        .gte("published_at", cutoff)
        .order("relevance_score", desc=True)
        .limit(MAX_CANDIDATES)
        .execute()
    )
    return result.data or []


def already_written(headline):
    result = supabase.table("posts").select("id").ilike("title", f"%{headline[:40]}%").limit(1).execute()
    return bool(result.data)


def pick_topic(candidates):
    for item in candidates:
        if not already_written(item["headline"]):
            return item
    return None


def make_slug(title):
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    slug = re.sub(r"\s+", "-", slug.strip())
    return re.sub(r"-+", "-", slug)[:80]


# Note: JSON block uses {{ and }} to escape braces in Python .format() strings
WRITER_PROMPT = """You are Veltix, the AI persona behind Veltrix Collective (veltrixcollective.com).

Write a complete SEO blog post about this AI news story.

Headline: {headline}
Source: {source_name}
Summary: {summary}
Source URL: {source_url}

Requirements:
- ~{word_count} words
- First person plural. "we track", "we tested", "our rankings".
- Slightly irreverent. Never corporate. Specific about what matters and why.
- Weave in "you need AI to keep up with AI" naturally at least once
- Structure: hook intro -> what happened -> why it matters -> what to do -> CTA
- CTA links to veltrixcollective.com/tools or veltrixcollective.com/insider
- 2-3 H2 headings using ## markdown
- Analyse and add perspective. Do NOT reproduce the source article verbatim.

Append this JSON block at the very end of your response:
```json
{{
  "title": "SEO title 60 chars max",
  "excerpt": "2-sentence preview 150 chars max",
  "meta_title": "Meta title 60 chars max",
  "meta_description": "Meta description 155 chars max",
  "tags": ["tag1", "tag2", "tag3"],
  "category": "ai-tools OR llm-news OR industry OR automation OR research"
}}
```"""


def generate_post(topic):
    log.info(f"Generating post for: {topic['headline'][:70]}")
    prompt = WRITER_PROMPT.format(
        headline=topic["headline"],
        source_name=topic["source_name"],
        summary=topic.get("summary", ""),
        source_url=topic["source_url"],
        word_count=TARGET_WORD_COUNT,
    )
    raw = call_ai(prompt, max_tokens=2500, quality=True)

    # Split content from trailing JSON metadata block
    content, meta = raw, {}
    m = re.search(r"```json\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if m:
        try:
            meta = json.loads(m.group(1))
            content = raw[:m.start()].strip()
        except json.JSONDecodeError:
            log.warning("  Metadata JSON parse failed — using fallback values")

    title = meta.get("title") or topic["headline"][:100]
    slug  = make_slug(title)
    if supabase.table("posts").select("id").eq("slug", slug).limit(1).execute().data:
        slug = f"{slug}-{hashlib.sha256(title.encode()).hexdigest()[:6]}"

    return {
        "title":            title,
        "slug":             slug,
        "content":          content,
        "excerpt":          meta.get("excerpt", content[:200]),
        "meta_title":       meta.get("meta_title", title),
        "meta_description": meta.get("meta_description", ""),
        "tags":             meta.get("tags", []),
        "category":         meta.get("category", "ai-tools"),
        "status":           "draft",
        "is_paywalled":     False,
    }


def save_post(post):
    try:
        result = supabase.table("posts").insert(post).execute()
        pid = result.data[0]["id"]
        log.info(f"  Saved post ID {pid}: {post['title'][:60]}")
        return pid
    except Exception as e:
        log.error(f"  Failed to save post: {e}")
        return None


def log_run(status, message, records=0):
    try:
        supabase.table("automation_logs").insert({
            "script_name": "writer", "status": status,
            "message": message, "records_processed": records,
        }).execute()
    except Exception as e:
        log.warning(f"Automation log failed: {e}")


def main():
    log.info("=" * 60)
    log.info("Writer starting")
    log.info("=" * 60)

    candidates = fetch_candidates()
    log.info(f"Found {len(candidates)} high-scoring items from last {NEWS_LOOKBACK_HOURS}h")

    if not candidates:
        log_run("skipped", "No qualifying news items"); return

    topic = pick_topic(candidates)
    if not topic:
        log_run("skipped", "All candidates already written"); return

    log.info(f"Selected: {topic['headline']}")
    post = generate_post(topic)
    if not post:
        log_run("error", "Post generation failed"); return

    post_id = save_post(post)
    if post_id:
        log_run("success", f"Draft created: {post['title'][:80]}", 1)
        log.info(f"Writer complete — post ID {post_id} saved as draft")
    else:
        log_run("error", "Failed to save post")


if __name__ == "__main__":
    main()