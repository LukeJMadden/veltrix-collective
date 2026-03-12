#!/usr/bin/env python3
"""
write_post.py — Veltrix Content Pipeline
Daily. Finds trending AI topics via pytrends, picks the best opportunity,
writes a 1200-word post in Veltrix voice, saves as draft to Supabase.
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import json
from datetime import datetime, timezone
from pytrends.request import TrendReq
from utils.common import get_logger, get_supabase, get_anthropic, log_run, VELTRIX_SYSTEM_PROMPT, slugify, now_utc

logger = get_logger("write_post")

POST_TEMPLATES = [
    "Top 10 {topic} Tools Ranked — Tested by Veltrix",
    "Best AI Tools for {topic} in 2025 — Veltrix Rankings",
    "The {topic} AI Tools Worth Your Time (And the Ones That Aren't)",
    "{topic} vs Everything: Veltrix Breaks Down the Best Options",
]

def get_trending_topics() -> list[str]:
    """Get trending AI-related search terms via pytrends."""
    try:
        pytrends = TrendReq(hl='en-US', tz=360, timeout=(10, 30))
        # Related topics to "AI tools"
        pytrends.build_payload(
            ["AI tools", "Claude API", "ChatGPT", "LLM", "AI assistant"],
            cat=0, timeframe='now 7-d', geo='', gprop=''
        )
        related = pytrends.related_queries()
        topics = []
        for kw in ["AI tools", "Claude API", "ChatGPT"]:
            if kw in related and related[kw]["top"] is not None:
                top_queries = related[kw]["top"]["query"].tolist()[:5]
                topics.extend(top_queries)

        # Deduplicate and clean
        seen = set()
        unique = []
        for t in topics:
            clean = t.strip()
            if clean.lower() not in seen and len(clean) > 3:
                seen.add(clean.lower())
                unique.append(clean)

        logger.info(f"Found {len(unique)} trending topics: {unique[:5]}")
        return unique[:10]
    except Exception as e:
        logger.warning(f"pytrends failed: {e}, using fallback topics")
        return [
            "Claude API automation",
            "AI tools for content creators",
            "LLM comparison 2025",
            "AI productivity tools",
            "best AI coding assistants",
        ]

def pick_best_topic(client, topics: list[str], supabase) -> str:
    """Use Claude to pick the highest-opportunity topic we haven't covered."""
    # Check recently published posts to avoid repeats
    recent = supabase.table("posts").select("title").eq("status", "published").order("created_at", ascending=False).limit(10).execute()
    recent_titles = [p["title"] for p in recent.data]

    msg = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": f"""You are a content strategist for Veltrix Collective, an AI tools hub.

Trending topics this week: {json.dumps(topics)}
Recently published posts to avoid repeating: {json.dumps(recent_titles)}

Pick the SINGLE best topic from the trending list to write about.
Criteria: high search intent, not recently covered, AI tools angle possible.

Return ONLY the topic text, nothing else."""
        }]
    )
    chosen = msg.content[0].text.strip()
    logger.info(f"Chosen topic: {chosen}")
    return chosen

def write_post(client, topic: str, supabase) -> dict:
    """Generate a full 1200-word post in Veltrix voice."""
    # Get affiliate tools from DB
    tools = supabase.table("tools").select("name,affiliate_url,description,category,score").order("score", ascending=False).limit(15).execute()
    tool_list = "\n".join([f"- {t['name']}: {t['description'][:80]} (affiliate: {t['affiliate_url'] or t.get('url', '')})" for t in tools.data])

    veltrix_tools = supabase.table("tools").select("name,affiliate_url,description").eq("is_veltrix_tool", True).limit(3).execute()
    veltrix_pick = veltrix_tools.data[0] if veltrix_tools.data else {"name": "AI Matchmaker", "affiliate_url": "https://www.veltrixcollective.com/tools/matchmaker", "description": "Find the right tool for any AI task"}

    import random
    title_template = random.choice(POST_TEMPLATES)
    title = title_template.format(topic=topic)

    msg = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2500,
        system=VELTRIX_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Write a complete 1,200-word blog post for Veltrix Collective.

Title: "{title}"
Topic: {topic}

Available tools to reference (use affiliate links where available):
{tool_list}

REQUIRED STRUCTURE:
1. Intro paragraph — Veltrix voice, reference "we track" or "we tested"
2. Main listicle — 8-10 tools/options with 2-3 sentence descriptions each
3. "Veltrix Pick" section at the end — highlight: {veltrix_pick['name']} ({veltrix_pick['description']})
4. CTA closing: "Want the tools Veltrix uses but doesn't publish? Unlock the insider guides → https://www.veltrixcollective.com/free"

Format as clean HTML (use <h2>, <p>, <strong>, <a href> tags). No markdown.
Include affiliate links naturally where relevant.
Write as Veltrix. First person. Direct. No fluff."""
        }]
    )

    content = msg.content[0].text.strip()
    slug = slugify(title)

    # Generate meta description
    meta_msg = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=100,
        messages=[{
            "role": "user",
            "content": f"Write a 155-character meta description for this post title: '{title}'. Be direct and include the main keyword. No quotes."
        }]
    )
    meta_desc = meta_msg.content[0].text.strip()[:155]

    # Generate excerpt
    excerpt = content[:300].replace('<', '').replace('>', '').replace('  ', ' ')[:200] + "..."

    return {
        "title": title,
        "slug": slug,
        "content": content,
        "excerpt": excerpt,
        "meta_title": title[:60],
        "meta_description": meta_desc,
        "status": "draft",
        "category": "tools",
        "tags": ["ai-tools", slugify(topic), "rankings"],
        "is_paywalled": False,
        "created_at": now_utc(),
    }

def main():
    logger.info("=== Veltrix Content Pipeline Starting ===")
    supabase = get_supabase()
    client = get_anthropic()

    topics = get_trending_topics()
    topic = pick_best_topic(client, topics, supabase)
    post = write_post(client, topic, supabase)

    # Save to Supabase
    supabase.table("posts").insert(post).execute()
    logger.info(f"Draft saved: '{post['title']}'")
    log_run(supabase, "write_post", "success", f"Draft: {post['title']}", 1)
    print(f"::notice title=Post Created::Draft saved: {post['title']}")

if __name__ == "__main__":
    main()
