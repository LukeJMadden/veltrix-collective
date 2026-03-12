#!/usr/bin/env python3
"""
send_newsletter.py — Veltrix Weekly Newsletter
Every Tuesday 8am UTC. Pulls top news, tool of week, latest post,
writes in Veltrix voice, sends to all subscriber lists via Brevo.
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timezone, timedelta
from utils.common import get_logger, get_supabase, get_anthropic, log_run, VELTRIX_SYSTEM_PROMPT, send_brevo_campaign_to_list

logger = get_logger("send_newsletter")

# Brevo list IDs — update these after creating lists in Brevo dashboard
BREVO_FREE_LIST_ID = int(os.environ.get("BREVO_FREE_LIST_ID", "2"))
BREVO_LIFETIME_LIST_ID = int(os.environ.get("BREVO_LIFETIME_LIST_ID", "3"))

def build_newsletter_html(content: dict, is_premium: bool = False) -> str:
    """Build the newsletter HTML from content sections."""
    news_items_html = "".join([
        f"""<div style="margin-bottom:16px;padding:12px 16px;background:#0f1318;border-left:3px solid #00c2ff;border-radius:4px;">
          <a href="{item.get('source_url','#')}" style="color:#fff;font-weight:600;text-decoration:none;font-size:14px;">{item['headline']}</a>
          <p style="color:#8b9ab0;font-size:13px;margin:6px 0 0;line-height:1.5;">{item['summary'][:180]}...</p>
          <span style="color:#4a5568;font-size:11px;">{item.get('source_name','')}</span>
        </div>"""
        for item in content["top_news"]
    ])

    premium_section = ""
    if is_premium and content.get("guide_excerpt"):
        premium_section = f"""
        <div style="padding:20px;background:rgba(0,194,255,0.05);border:1px solid rgba(0,194,255,0.2);border-radius:8px;margin:24px 0;">
          <p style="color:#00c2ff;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;">INSIDER EXCLUSIVE</p>
          <h3 style="color:#fff;font-size:16px;font-weight:700;margin-bottom:12px;">{content.get('guide_title','')}</h3>
          <p style="color:#8b9ab0;font-size:14px;line-height:1.6;">{content['guide_excerpt']}</p>
          <a href="https://www.veltrixcollective.com/guides" style="display:inline-block;margin-top:12px;color:#00c2ff;font-size:13px;font-weight:600;text-decoration:none;">Read the full guide →</a>
        </div>"""

    return f"""
<div style="max-width:600px;margin:0 auto;font-family:Inter,-apple-system,sans-serif;color:#fff;background:#080b0f;border-radius:12px;overflow:hidden;border:1px solid #1e2733;">
  <!-- Header -->
  <div style="padding:24px 32px;border-bottom:1px solid #1e2733;background:#0f1318;">
    <span style="font-size:20px;font-weight:800;">Veltrix<span style="color:#00c2ff;">.</span></span>
    <p style="color:#8b9ab0;font-size:12px;margin:4px 0 0;">Weekly Intelligence Report · {datetime.now().strftime('%B %d, %Y')}</p>
  </div>

  <div style="padding:32px;">
    <!-- Intro -->
    <p style="color:#8b9ab0;font-size:15px;line-height:1.6;margin-bottom:32px;">{content['intro']}</p>

    <!-- Top News -->
    <h2 style="color:#fff;font-size:16px;font-weight:700;margin-bottom:16px;display:flex;align-items:center;gap:8px;">
      📡 This week in AI
    </h2>
    {news_items_html}

    <!-- Tool of the Week -->
    <div style="margin:32px 0;padding:20px;background:#0f1318;border:1px solid #1e2733;border-radius:8px;">
      <p style="color:#00c2ff;font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:8px;">⚡ TOOL OF THE WEEK</p>
      <h3 style="color:#fff;font-size:16px;font-weight:700;margin-bottom:8px;">{content['tool_of_week']['name']}</h3>
      <p style="color:#8b9ab0;font-size:14px;line-height:1.5;margin-bottom:12px;">{content['tool_of_week']['commentary']}</p>
      <a href="{content['tool_of_week']['url']}" style="display:inline-block;padding:8px 16px;background:#00c2ff;color:#000;border-radius:6px;text-decoration:none;font-weight:600;font-size:13px;">Try it →</a>
    </div>

    {premium_section}

    <!-- Latest Post -->
    <div style="margin:24px 0;">
      <p style="color:#8b9ab0;font-size:12px;font-weight:600;text-transform:uppercase;margin-bottom:8px;">LATEST FROM THE BLOG</p>
      <a href="https://www.veltrixcollective.com/posts/{content['latest_post']['slug']}" style="color:#fff;font-size:15px;font-weight:600;text-decoration:none;">{content['latest_post']['title']}</a>
      <p style="color:#8b9ab0;font-size:13px;margin:6px 0 0;line-height:1.5;">{content['latest_post']['excerpt'][:150]}...</p>
    </div>

    <!-- Tease -->
    <div style="padding:16px;background:#0f1318;border:1px solid #1e2733;border-radius:8px;margin:24px 0;font-size:13px;color:#8b9ab0;font-style:italic;">
      {content['tease']}
    </div>

    <!-- CTA -->
    <div style="text-align:center;padding:24px 0;">
      <a href="https://www.veltrixcollective.com/free" style="display:inline-block;padding:12px 28px;background:#00c2ff;color:#000;border-radius:8px;text-decoration:none;font-weight:700;font-size:14px;">Insider Access — $9.99 lifetime →</a>
      <p style="color:#4a5568;font-size:11px;margin-top:8px;">First 100 members. Then $19.99.</p>
    </div>
  </div>

  <!-- Footer -->
  <div style="padding:16px 32px;border-top:1px solid #1e2733;background:#080b0f;">
    <p style="color:#4a5568;font-size:11px;text-align:center;">
      Veltrix Collective · <a href="https://www.veltrixcollective.com" style="color:#4a5568;">veltrixcollective.com</a>
      · <a href="{{{{unsubscribeUrl}}}}" style="color:#4a5568;">Unsubscribe</a>
    </p>
  </div>
</div>"""

def get_newsletter_content(client, supabase) -> dict:
    """Assemble content for the newsletter."""
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    # Top 5 news items
    news = supabase.table("news").select("*").gte("published_at", week_ago).order("relevance_score", ascending=False).order("published_at", ascending=False).limit(5).execute().data

    # Most-upvoted tool this week
    top_tool = supabase.table("tools").select("*").order("votes", ascending=False).limit(1).execute().data
    tool = top_tool[0] if top_tool else {"name": "Claude", "description": "The model powering this whole operation.", "affiliate_url": "https://claude.ai", "url": "https://claude.ai"}

    # Latest published post
    post = supabase.table("posts").select("title,slug,excerpt").eq("status", "published").order("published_at", ascending=False).limit(1).execute().data
    latest_post = post[0] if post else {"title": "Veltrix Rankings Update", "slug": "rankings-update", "excerpt": "The weekly rankings update is live."}

    # Latest paywalled guide title for premium tease
    guide = supabase.table("posts").select("title,content").eq("is_paywalled", True).eq("status", "published").order("published_at", ascending=False).limit(1).execute().data
    guide_title = guide[0]["title"] if guide else "Insider Guide"
    guide_excerpt = guide[0]["content"][:300] if guide else ""

    # Generate with Claude
    most_interesting_headline = news[0]["headline"] if news else "AI moves fast this week"
    subject = f"Veltrix Weekly: {most_interesting_headline[:60]}"

    msg = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=600,
        system=VELTRIX_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Write content for the Veltrix Weekly newsletter.

Top news this week: {most_interesting_headline}
Tool of the week: {tool['name']} — {tool.get('description','')[:100]}

Write:
1. A 2-sentence newsletter intro in Veltrix voice
2. A 2-sentence "tool of the week" commentary for {tool['name']}
3. A one-liner tease ("Something's coming next week...") — mysterious, not specific
4. A 3-word analysis of {tool['name']} for this week

Return JSON only:
{{"intro": "...", "tool_commentary": "...", "tease": "..."}}"""
        }]
    )

    import json, re
    text = msg.content[0].text.strip()
    try:
        generated = json.loads(text)
    except Exception:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        generated = json.loads(match.group()) if match else {"intro": "The AI landscape moved fast this week.", "tool_commentary": f"{tool['name']} continues to impress.", "tease": "Something's coming next week — stay tuned."}

    return {
        "subject": subject,
        "top_news": news,
        "tool_of_week": {
            "name": tool["name"],
            "commentary": generated.get("tool_commentary", ""),
            "url": tool.get("affiliate_url") or tool.get("url", "#"),
        },
        "latest_post": latest_post,
        "guide_title": guide_title,
        "guide_excerpt": guide_excerpt,
        "intro": generated.get("intro", ""),
        "tease": generated.get("tease", "Something's coming next week."),
    }

def main():
    logger.info("=== Veltrix Newsletter Starting ===")
    supabase = get_supabase()
    client = get_anthropic()

    content = get_newsletter_content(client, supabase)
    subject = content["subject"]

    # Build HTML versions
    free_html = build_newsletter_html(content, is_premium=False)
    premium_html = build_newsletter_html(content, is_premium=True)

    # Send to free list
    free_campaign = send_brevo_campaign_to_list(BREVO_FREE_LIST_ID, subject, free_html, preview_text=content["intro"][:90])
    logger.info(f"Free newsletter sent. Campaign ID: {free_campaign}")

    # Send premium version to lifetime members
    premium_subject = f"[Insider] {subject}"
    premium_campaign = send_brevo_campaign_to_list(BREVO_LIFETIME_LIST_ID, premium_subject, premium_html, preview_text=content["intro"][:90])
    logger.info(f"Premium newsletter sent. Campaign ID: {premium_campaign}")

    # Log to DB
    supabase.table("newsletters").insert({
        "subject": subject,
        "content_html": free_html[:5000],
        "content_premium_html": premium_html[:5000],
        "status": "sent",
        "sent_at": datetime.now(timezone.utc).isoformat(),
    }).execute()

    log_run(supabase, "send_newsletter", "success", f"Sent: {subject}", 2)
    logger.info("Newsletter complete.")

if __name__ == "__main__":
    main()
