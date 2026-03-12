#!/usr/bin/env python3
"""
weekly_report.py — Veltrix Performance Report
Every Monday 7am UTC. Pulls key metrics, Claude writes a plain-English
summary with recommendations, emails it to the owner.
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
from datetime import datetime, timezone, timedelta
from utils.common import get_logger, get_supabase, get_anthropic, log_run, send_brevo_email

logger = get_logger("weekly_report")

OWNER_EMAIL = os.environ.get("OWNER_EMAIL", "lukejmadden@outlook.com")

def get_supabase_metrics(supabase) -> dict:
    """Pull key metrics from Supabase."""
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    two_weeks_ago = (datetime.now(timezone.utc) - timedelta(days=14)).isoformat()

    # New users this week vs last week
    new_users_this = len(supabase.table("users").select("id", count="exact").gte("created_at", week_ago).execute().data or [])
    new_users_last = len(supabase.table("users").select("id", count="exact").gte("created_at", two_weeks_ago).lt("created_at", week_ago).execute().data or [])

    # Lifetime members
    lifetime = len(supabase.table("users").select("id", count="exact").eq("tier", "lifetime").execute().data or [])

    # Total subscribers
    total_users = len(supabase.table("users").select("id", count="exact").execute().data or [])

    # Top tool this week
    top_tool = supabase.table("tools").select("name,votes,score").order("votes", ascending=False).limit(1).execute().data
    top_tool_name = top_tool[0]["name"] if top_tool else "unknown"

    # Most viewed post
    top_post = supabase.table("posts").select("title,view_count").eq("status", "published").order("view_count", ascending=False).limit(1).execute().data
    top_post_title = top_post[0]["title"] if top_post else "unknown"
    top_post_views = top_post[0]["view_count"] if top_post else 0

    # News items added
    news_count = len(supabase.table("news").select("id", count="exact").gte("published_at", week_ago).execute().data or [])

    # Posts published
    posts_published = len(supabase.table("posts").select("id", count="exact").eq("status", "published").gte("published_at", week_ago).execute().data or [])

    # Support tickets
    support_tickets = len(supabase.table("support_logs").select("id", count="exact").gte("created_at", week_ago).execute().data or [])

    return {
        "new_users": new_users_this,
        "new_users_last_week": new_users_last,
        "total_users": total_users,
        "lifetime_members": lifetime,
        "top_tool": top_tool_name,
        "top_post": top_post_title,
        "top_post_views": top_post_views,
        "news_items": news_count,
        "posts_published": posts_published,
        "support_tickets": support_tickets,
    }

def get_revenue_estimate(metrics: dict) -> str:
    """Estimate weekly revenue from lifetime member count."""
    # Simple estimate: $9.99 per new lifetime member this week
    # (LemonSqueezy API could be integrated for real numbers)
    return f"~${metrics['lifetime_members'] * 9.99:.0f} cumulative (based on {metrics['lifetime_members']} lifetime members × $9.99)"

def build_report_html(analysis: str, metrics: dict, revenue: str) -> str:
    week_str = datetime.now().strftime("%B %d, %Y")
    growth = ((metrics["new_users"] - metrics["new_users_last_week"]) / max(metrics["new_users_last_week"], 1) * 100)
    growth_str = f"+{growth:.0f}%" if growth >= 0 else f"{growth:.0f}%"
    growth_color = "#00e676" if growth >= 0 else "#ff4444"

    return f"""
<div style="max-width:600px;margin:0 auto;font-family:Inter,sans-serif;color:#fff;background:#080b0f;padding:32px;border-radius:12px;border:1px solid #1e2733;">
  <span style="font-size:18px;font-weight:800;">Veltrix<span style="color:#00c2ff;">.</span> Weekly Report</span>
  <p style="color:#8b9ab0;font-size:12px;margin:4px 0 24px;">{week_str}</p>

  <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:24px;">
    {chr(10).join([f'''<div style="padding:16px;background:#0f1318;border:1px solid #1e2733;border-radius:8px;">
      <p style="color:#8b9ab0;font-size:11px;margin:0 0 4px;">{label}</p>
      <p style="color:{color};font-size:20px;font-weight:700;margin:0;">{value}</p>
    </div>''' for label, value, color in [
        ("New users this week", metrics["new_users"], "#00c2ff"),
        ("WoW growth", growth_str, growth_color),
        ("Total subscribers", metrics["total_users"], "#fff"),
        ("Lifetime members", metrics["lifetime_members"], "#00e676"),
        ("News items added", metrics["news_items"], "#fff"),
        ("Posts published", metrics["posts_published"], "#fff"),
    ]])}
  </div>

  <div style="padding:16px;background:#0f1318;border:1px solid #1e2733;border-radius:8px;margin-bottom:24px;">
    <p style="color:#8b9ab0;font-size:11px;margin:0 0 4px;">REVENUE ESTIMATE</p>
    <p style="color:#00e676;font-size:16px;font-weight:600;margin:0;">{revenue}</p>
  </div>

  <div style="margin-bottom:24px;">
    <p style="color:#8b9ab0;font-size:11px;font-weight:600;text-transform:uppercase;margin-bottom:8px;">VELTIX ANALYSIS</p>
    <div style="font-size:14px;color:#8b9ab0;line-height:1.7;">{analysis.replace(chr(10), '<br>')}</div>
  </div>

  <div style="padding:12px 16px;background:#0f1318;border-left:3px solid #00c2ff;border-radius:4px;font-size:13px;color:#8b9ab0;">
    <strong style="color:#fff;">Top tool this week:</strong> {metrics['top_tool']}<br>
    <strong style="color:#fff;">Top post:</strong> {metrics['top_post']} ({metrics['top_post_views']} views)<br>
    <strong style="color:#fff;">Support tickets:</strong> {metrics['support_tickets']}
  </div>
</div>"""

def main():
    logger.info("=== Veltrix Weekly Report Starting ===")
    supabase = get_supabase()
    client = get_anthropic()

    metrics = get_supabase_metrics(supabase)
    revenue = get_revenue_estimate(metrics)
    logger.info(f"Metrics: {metrics}")

    # Claude analysis
    msg = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=400,
        messages=[{
            "role": "user",
            "content": f"""You are Veltrix's performance analyst. Write a 3-4 sentence plain-English weekly summary.

Metrics this week:
- New users: {metrics['new_users']} (last week: {metrics['new_users_last_week']})
- Total subscribers: {metrics['total_users']}
- Lifetime members: {metrics['lifetime_members']}
- Top tool: {metrics['top_tool']}
- Top post: {metrics['top_post']} ({metrics['top_post_views']} views)
- News items added: {metrics['news_items']}
- Posts published: {metrics['posts_published']}
- Support tickets: {metrics['support_tickets']}

Write: 1 sentence on what went well, 1 on what needs attention, 1 concrete recommendation for next week.
Example: "This week: X new users (+Y%), top post was Z. Tool engagement dropped slightly — likely needs fresh content. Recommendation: write more content about [topic] based on traffic data."

Be specific. No fluff."""
        }]
    )
    analysis = msg.content[0].text.strip()

    html = build_report_html(analysis, metrics, revenue)
    send_brevo_email(OWNER_EMAIL, f"Veltrix Weekly Report — {datetime.now().strftime('%b %d')}", html, from_name="Veltrix Reports")

    logger.info(f"Report sent to {OWNER_EMAIL}")
    log_run(supabase, "weekly_report", "success", f"Sent to {OWNER_EMAIL}", 1)

if __name__ == "__main__":
    main()
