#!/usr/bin/env python3
"""
triage_support.py — Veltrix AI Support Triage
Every 2 hours. Checks Brevo inbox, classifies emails,
auto-resolves what it can, logs everything.
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import json, requests
from datetime import datetime, timezone
from utils.common import get_logger, get_supabase, get_anthropic, log_run, VELTRIX_SYSTEM_PROMPT, send_brevo_email

logger = get_logger("triage_support")

BREVO_API_KEY = os.environ.get("BREVO_API_KEY", "")
LEMON_SQUEEZY_API_KEY = os.environ.get("LEMON_SQUEEZY_API_KEY", "")

VELTRIX_FAQ = """
- Lifetime access: $9.99 first 100 members, $19.99 after
- Includes: all guides + Discord + unlimited tools + all future guides
- Discord invite: sent by email within 5 minutes of purchase
- Refund policy: 7 days, no questions, just email veltix@veltrixcollective.com
- Tool daily limits: 5 matchmaker, 3 LLM tests (unlimited with Insider)
- How to access guides: sign in at veltrixcollective.com/guides
"""

def get_support_emails() -> list[dict]:
    """Fetch unread emails from Brevo inbox."""
    try:
        res = requests.get(
            "https://api.brevo.com/v3/inbound/events",
            headers={"api-key": BREVO_API_KEY},
            params={"limit": 20, "offset": 0},
            timeout=30,
        )
        if res.status_code != 200:
            logger.warning(f"Brevo inbox fetch failed: {res.status_code}")
            return []
        return res.json().get("events", [])
    except Exception as e:
        logger.warning(f"Inbox fetch error: {e}")
        return []

def classify_email(client, email: dict) -> dict:
    """Classify a support email."""
    msg = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": f"""Classify this support email for Veltrix Collective.

Subject: {email.get('subject', 'No subject')}
Body: {email.get('textContent', email.get('htmlContent', ''))[:500]}
From: {email.get('sender', {}).get('email', '')}

Categories: refund | access-issue | question | bug | spam | other

Return JSON only: {{"category": "question", "urgency": "normal", "summary": "one sentence"}}"""
        }]
    )
    try:
        return json.loads(msg.content[0].text.strip())
    except Exception:
        return {"category": "other", "urgency": "normal", "summary": "Could not classify"}

def handle_refund(client, email: dict, supabase) -> str:
    """Process a refund request."""
    customer_email = email.get("sender", {}).get("email", "")
    # Look up their order in Supabase
    user = supabase.table("users").select("*").eq("email", customer_email).execute().data
    if user and user[0].get("lemon_squeezy_order_id"):
        order_id = user[0]["lemon_squeezy_order_id"]
        # Trigger Lemon Squeezy refund API
        try:
            res = requests.post(
                f"https://api.lemonsqueezy.com/v1/orders/{order_id}/refund",
                headers={"Authorization": f"Bearer {LEMON_SQUEEZY_API_KEY}", "Content-Type": "application/json"},
                timeout=30,
            )
            if res.status_code in [200, 201]:
                supabase.table("users").update({"tier": "free"}).eq("email", customer_email).execute()
                return "Refund processed and confirmed."
        except Exception as e:
            logger.warning(f"Refund API failed: {e}")
    return "Refund request received. Processing within 24 hours."

def generate_reply(client, email: dict, category: str, extra_context: str = "") -> str:
    """Generate an AI reply for a support email."""
    msg = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=300,
        system=VELTRIX_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Write a support reply for Veltrix Collective.

Category: {category}
Customer email body: {email.get('textContent', '')[:400]}
{f"Resolution: {extra_context}" if extra_context else ""}

FAQ:
{VELTRIX_FAQ}

Write a helpful, direct reply in Veltrix voice. 3-5 sentences.
If you can't fully resolve it, say: "I'll flag this for personal review — you'll hear back within 24 hours."
Do not invent information not in the FAQ."""
        }]
    )
    return msg.content[0].text.strip()

def main():
    logger.info("=== Veltrix Support Triage Starting ===")
    supabase = get_supabase()
    client = get_anthropic()

    emails = get_support_emails()
    logger.info(f"Found {len(emails)} emails to process")

    processed = 0
    for email in emails:
        sender = email.get("sender", {}).get("email", "unknown")
        subject = email.get("subject", "No subject")

        if sender in ["veltix@veltrixcollective.com", ""]:
            continue

        classification = classify_email(client, email)
        category = classification.get("category", "other")
        logger.info(f"  {sender} | {category} | {subject[:40]}")

        resolution = ""
        auto_resolved = False

        if category == "refund":
            resolution = handle_refund(client, email, supabase)
            auto_resolved = True
        elif category == "spam":
            logger.info(f"  Skipping spam from {sender}")
            continue
        elif category in ["question", "access-issue"]:
            resolution = ""
            auto_resolved = True

        # Generate reply
        reply = generate_reply(client, email, category, resolution)

        # Send reply
        if auto_resolved and sender != "unknown":
            try:
                send_brevo_email(
                    to_email=sender,
                    subject=f"Re: {subject}",
                    html_content=f"""
<div style="max-width:520px;margin:0 auto;font-family:Inter,sans-serif;color:#fff;background:#080b0f;padding:32px;border-radius:12px;border:1px solid #1e2733;">
  <span style="font-size:18px;font-weight:800;">Veltrix<span style="color:#00c2ff;">.</span></span>
  <div style="margin:24px 0;font-size:15px;color:#8b9ab0;line-height:1.7;">{reply.replace(chr(10), '<br>')}</div>
  <p style="color:#4a5568;font-size:11px;margin-top:24px;">— Veltix · Veltrix Collective</p>
</div>""",
                )
            except Exception as e:
                logger.warning(f"  Reply send failed: {e}")

        # Log to Supabase
        supabase.table("support_logs").insert({
            "email": sender,
            "category": category,
            "subject": subject[:200],
            "body_snippet": email.get("textContent", "")[:300],
            "resolution": resolution or reply[:200],
            "auto_resolved": auto_resolved,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()

        processed += 1

    logger.info(f"Processed {processed} emails.")
    log_run(supabase, "triage_support", "success", f"Processed {processed} emails", processed)

if __name__ == "__main__":
    main()
