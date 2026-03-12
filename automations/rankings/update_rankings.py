#!/usr/bin/env python3
"""
update_rankings.py — Veltrix Rankings Update
Weekly (Sundays 3am UTC). Uses Claude to re-score all tools based on
recent news, benchmark data, and sentiment. Flags new tools for addition.
Also generates a "Rankings Movers" post automatically.
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import json
from datetime import datetime, timezone, timedelta
from utils.common import get_logger, get_supabase, get_anthropic, log_run, VELTRIX_SYSTEM_PROMPT, slugify, now_utc

logger = get_logger("update_rankings")

def score_tool(client, tool: dict, recent_news: list[dict]) -> dict:
    """Ask Claude to re-score a tool based on recent data."""
    relevant_news = [n for n in recent_news
                     if tool["name"].lower() in (n.get("headline","") + n.get("summary","")).lower()][:5]

    news_context = "\n".join([f"- {n['headline']}: {n['summary'][:100]}" for n in relevant_news]) if relevant_news else "No recent news found."

    msg = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": f"""Rate this AI tool on a scale of 0-100 for the current week.

Tool: {tool['name']}
Category: {tool.get('category', 'unknown')}
Current score: {tool.get('score', 50)}
Recent news/mentions: {news_context}

Consider: user adoption, feature releases, community sentiment, benchmark performance, pricing changes.
Return ONLY a JSON object: {{"score": 85, "reason": "one sentence reason"}}
No markdown. Raw JSON only."""
        }]
    )
    try:
        result = json.loads(msg.content[0].text.strip())
        return {"score": min(100, max(0, float(result.get("score", tool.get("score", 50))))), "reason": result.get("reason", "")}
    except Exception:
        return {"score": tool.get("score", 50), "reason": "Score unchanged"}

def update_llm_rankings(client, supabase):
    """Update LLM rankings based on latest benchmark data."""
    llms = supabase.table("llm_rankings").select("*").execute().data

    for llm in llms:
        msg = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=300,
            messages=[{
                "role": "user",
                "content": f"""Update the scores for {llm['model_name']} by {llm['provider']} based on current knowledge.
Current scores: overall={llm['score_overall']}, coding={llm['score_coding']}, reasoning={llm['score_reasoning']}, creativity={llm['score_creativity']}, speed={llm['score_speed']}, cost_efficiency={llm['score_cost_efficiency']}

Return ONLY JSON (no markdown):
{{"score_overall": 90, "score_coding": 88, "score_reasoning": 92, "score_creativity": 85, "score_speed": 75, "score_cost_efficiency": 70}}"""
            }]
        )
        try:
            scores = json.loads(msg.content[0].text.strip())
            supabase.table("llm_rankings").update({**scores, "updated_at": now_utc()}).eq("id", llm["id"]).execute()
            logger.info(f"  Updated {llm['model_name']}: overall={scores.get('score_overall')}")
        except Exception as e:
            logger.warning(f"  Failed to update {llm['model_name']}: {e}")

def generate_movers_post(client, supabase, score_changes: list[dict]) -> None:
    """Auto-generate a 'Rankings Movers' blog post."""
    if not score_changes:
        return

    top_movers = sorted(score_changes, key=lambda x: abs(x["delta"]), reverse=True)[:5]
    movers_text = "\n".join([f"- {m['name']}: {'+' if m['delta'] > 0 else ''}{m['delta']:.1f} points. {m['reason']}" for m in top_movers])

    msg = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1000,
        system=VELTRIX_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Write a 400-word "Rankings Update" post for Veltrix Collective.
This week's biggest movers in AI tools:
{movers_text}

Include:
- Brief intro on what drove changes
- Each mover with context
- CTA: "See the full live rankings at https://www.veltrixcollective.com/tools"

Format as clean HTML (<h2>, <p>, <strong>). Be specific. Veltrix voice."""
        }]
    )

    content = msg.content[0].text.strip()
    date_str = datetime.now().strftime("%B %d, %Y")
    title = f"AI Tools Rankings Update — Week of {date_str}"

    supabase.table("posts").insert({
        "title": title,
        "slug": slugify(title),
        "content": content,
        "excerpt": f"This week's biggest movers in AI tools. {top_movers[0]['name']} saw the biggest change.",
        "status": "published",
        "category": "rankings",
        "published_at": now_utc(),
        "created_at": now_utc(),
    }).execute()
    logger.info(f"Rankings movers post published: {title}")

def main():
    logger.info("=== Veltrix Rankings Update Starting ===")
    supabase = get_supabase()
    client = get_anthropic()

    # Get recent news for context
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    news = supabase.table("news").select("headline,summary").gte("published_at", week_ago).limit(100).execute().data

    # Get all tools
    tools = supabase.table("tools").select("*").order("score", ascending=False).execute().data
    logger.info(f"Scoring {len(tools)} tools...")

    score_changes = []
    updated = 0
    for tool in tools:
        result = score_tool(client, tool, news)
        new_score = result["score"]
        delta = new_score - (tool.get("score") or 50)

        if abs(delta) >= 1:  # Only update if score actually changed
            supabase.table("tools").update({"score": new_score, "updated_at": now_utc()}).eq("id", tool["id"]).execute()
            score_changes.append({"name": tool["name"], "delta": delta, "reason": result["reason"]})
            updated += 1
            logger.info(f"  {tool['name']}: {tool.get('score', 50):.0f} → {new_score:.0f} ({delta:+.1f})")

    # Update LLM rankings too
    logger.info("Updating LLM rankings...")
    update_llm_rankings(client, supabase)

    # Generate movers post
    if score_changes:
        generate_movers_post(client, supabase, score_changes)

    logger.info(f"Updated {updated} tools.")
    log_run(supabase, "update_rankings", "success", f"Updated {updated} tools", updated)

if __name__ == "__main__":
    main()
