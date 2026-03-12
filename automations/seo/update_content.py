#!/usr/bin/env python3
"""
update_content.py — Veltrix SEO Content Optimisation
Monthly. Finds lowest-traffic posts, rewrites and expands them,
republishes with updated date, generates fresh social posts.
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timezone, timedelta
from utils.common import get_logger, get_supabase, get_anthropic, log_run, VELTRIX_SYSTEM_PROMPT, slugify, now_utc

logger = get_logger("update_content")

def rewrite_post(client, post: dict) -> str:
    """Expand and refresh a post."""
    msg = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=3000,
        system=VELTRIX_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Rewrite and expand this Veltrix Collective post. Make it significantly better.

Current title: {post['title']}
Current content: {post.get('content', '')[:2000]}

Requirements:
- Keep the same title and main topic
- Expand to at least 1,500 words
- Update any outdated information
- Improve the structure with clearer headers
- Make the intro stronger — hook in the first sentence
- Add more specific tool recommendations with links
- Ensure CTA to Veltrix Insider Access at the end
- Veltrix voice throughout

Return clean HTML only (h2, h3, p, strong, a tags). No markdown."""
        }]
    )
    return msg.content[0].text.strip()

def generate_comparison_page(client, tool_a: dict, tool_b: dict) -> dict:
    """Generate programmatic SEO comparison page content."""
    msg = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=1200,
        system=VELTRIX_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Write a comparison page for Veltrix Collective.

Tool A: {tool_a['name']} — {tool_a.get('description','')}
Tool B: {tool_b['name']} — {tool_b.get('description','')}

Compare across 6 criteria: Price, Ease of Use, Features, Best For, Limitations, Veltrix Score
Format as clean HTML. Include a "Veltrix Verdict" section at the end recommending one.
Add CTA to Veltrix tools and insider access."""
        }]
    )

    content = msg.content[0].text.strip()
    slug = f"{slugify(tool_a['name'])}-vs-{slugify(tool_b['name'])}"
    meta = f"{tool_a['name']} vs {tool_b['name']}: Veltrix ranks and compares both tools across price, features, and use cases. See which one wins."[:155]

    return {"slug": slug, "content": content, "meta_description": meta, "tool_a_id": tool_a["id"], "tool_b_id": tool_b["id"]}

def build_comparison_pages(supabase, client, max_pages: int = 50):
    """Generate programmatic SEO comparison pages."""
    tools = supabase.table("tools").select("id,name,category,description,score").order("score", ascending=False).limit(20).execute().data

    existing = {r["slug"] for r in supabase.table("tool_comparisons").select("slug").execute().data}
    generated = 0

    for i, tool_a in enumerate(tools):
        for tool_b in tools[i+1:]:
            if tool_a["category"] == tool_b["category"] and generated < max_pages:
                slug = f"{slugify(tool_a['name'])}-vs-{slugify(tool_b['name'])}"
                if slug in existing:
                    continue

                try:
                    page = generate_comparison_page(client, tool_a, tool_b)
                    supabase.table("tool_comparisons").insert({**page, "created_at": now_utc(), "updated_at": now_utc()}).execute()
                    generated += 1
                    logger.info(f"  Generated: {slug}")
                except Exception as e:
                    logger.warning(f"  Failed {slug}: {e}")

    logger.info(f"Generated {generated} comparison pages")
    return generated

def main():
    logger.info("=== Veltrix SEO Update Starting ===")
    supabase = get_supabase()
    client = get_anthropic()

    # Update low-traffic posts
    posts = supabase.table("posts").select("*").eq("status", "published").eq("is_paywalled", False).order("view_count", ascending=True).limit(3).execute().data
    logger.info(f"Rewriting {len(posts)} low-traffic posts")

    updated = 0
    for post in posts:
        try:
            new_content = rewrite_post(client, post)
            supabase.table("posts").update({
                "content": new_content,
                "published_at": now_utc(),
                "updated_at": now_utc(),
            }).eq("id", post["id"]).execute()
            updated += 1
            logger.info(f"  Updated: {post['title']}")
        except Exception as e:
            logger.warning(f"  Failed to update {post['id']}: {e}")

    # Build comparison pages
    comp_generated = build_comparison_pages(supabase, client, max_pages=10)

    total = updated + comp_generated
    log_run(supabase, "update_content", "success", f"Updated {updated} posts, {comp_generated} comparison pages", total)

if __name__ == "__main__":
    main()
