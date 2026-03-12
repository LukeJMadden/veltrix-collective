#!/usr/bin/env python3
"""
send_goal_checkins.py — Veltrix Subscriber Intelligence: Goal Check-ins
Runs weekly. Finds users with goals set 7/30/90 days ago and sends
a personalised Veltrix check-in email. Tracks check-in count.
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timezone, timedelta
from utils.common import get_logger, get_supabase, get_anthropic, log_run, VELTRIX_SYSTEM_PROMPT, send_brevo_email

logger = get_logger("send_goal_checkins")

CHECK_IN_INTERVALS = [7, 30, 90]  # days after signup

def should_check_in(user: dict) -> bool:
    """Determine if a user is due for a check-in."""
    if not user.get("goal"):
        return False
    created = datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))
    days_since = (datetime.now(timezone.utc) - created).days
    last_check_count = user.get("goal_check_count", 0)

    # Check if we're at an interval milestone and haven't sent this one
    for interval in CHECK_IN_INTERVALS:
        if days_since >= interval and last_check_count < CHECK_IN_INTERVALS.index(interval) + 1:
            return True
    return False

def get_check_in_number(user: dict) -> int:
    return (user.get("goal_check_count") or 0) + 1

def generate_checkin_email(client, user: dict) -> dict:
    """Generate a personalised goal check-in email."""
    check_num = get_check_in_number(user)
    days_since = (datetime.now(timezone.utc) - datetime.fromisoformat(user["created_at"].replace("Z", "+00:00"))).days

    msg = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=400,
        system=VELTRIX_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Write a short, personal goal check-in email for a Veltrix subscriber.

Their goal: "{user['goal']}"
Days since they joined: {days_since}
Check-in number: {check_num}
Their tier: {user.get('tier', 'free')}

Write in Veltrix voice — warm, direct, no fluff. 3-4 sentences max.
Ask one specific question about their goal progress.
Include one relevant tool or resource recommendation.
If they're free tier, mention insider access naturally (not pushy).

Return JSON: {{"subject": "...", "body": "..."}}
No markdown. Raw JSON."""
        }]
    )
    import json, re
    text = msg.content[0].text.strip()
    try:
        return json.loads(text)
    except Exception:
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {
            "subject": f"Veltrix check-in — how's it going with {user['goal'][:30]}?",
            "body": f"Hey — Veltix here. {days_since} days in. How are you getting on with {user['goal']}? Reply and let me know."
        }

def build_checkin_html(body: str, referral_code: str) -> str:
    referral_url = f"https://www.veltrixcollective.com/subscribe?ref={referral_code}"
    return f"""
<div style="max-width:520px;margin:0 auto;font-family:Inter,-apple-system,sans-serif;color:#fff;background:#080b0f;padding:32px;border-radius:12px;border:1px solid #1e2733;">
  <span style="font-size:18px;font-weight:800;">Veltrix<span style="color:#00c2ff;">.</span></span>
  <div style="margin:24px 0;font-size:15px;color:#8b9ab0;line-height:1.7;">{body.replace(chr(10), '<br>')}</div>
  <div style="padding:16px;background:#0f1318;border:1px solid #1e2733;border-radius:8px;font-size:13px;color:#8b9ab0;margin-top:24px;">
    Your referral link: <a href="{referral_url}" style="color:#00c2ff;">{referral_url}</a><br>
    <span style="font-size:11px;color:#4a5568;">Share it — rewards come when people subscribe.</span>
  </div>
  <p style="color:#4a5568;font-size:11px;margin-top:24px;">— Veltix · <a href="https://www.veltrixcollective.com" style="color:#4a5568;">veltrixcollective.com</a> · <a href="{{{{unsubscribeUrl}}}}" style="color:#4a5568;">Unsubscribe</a></p>
</div>"""

def main():
    logger.info("=== Veltrix Goal Check-ins Starting ===")
    supabase = get_supabase()
    client = get_anthropic()

    # Get all users with goals
    users = supabase.table("users").select("*").not_.is_("goal", "null").execute().data
    logger.info(f"Found {len(users)} users with goals")

    sent = 0
    for user in users:
        if not should_check_in(user):
            continue

        try:
            email_content = generate_checkin_email(client, user)
            html = build_checkin_html(email_content["body"], user.get("referral_code", ""))

            send_brevo_email(user["email"], email_content["subject"], html)

            # Log check-in
            supabase.table("goal_checkins").insert({
                "user_id": user["id"],
                "email": user["email"],
                "goal": user["goal"],
                "checkin_number": get_check_in_number(user),
                "sent_at": datetime.now(timezone.utc).isoformat(),
            }).execute()

            # Update user
            supabase.table("users").update({
                "goal_check_count": (user.get("goal_check_count") or 0) + 1,
                "last_goal_check": datetime.now(timezone.utc).isoformat(),
            }).eq("id", user["id"]).execute()

            sent += 1
            logger.info(f"  Check-in sent to {user['email']}")
        except Exception as e:
            logger.warning(f"  Failed for {user['email']}: {e}")

    logger.info(f"Sent {sent} goal check-ins.")
    log_run(supabase, "send_goal_checkins", "success", f"Sent {sent} check-ins", sent)

if __name__ == "__main__":
    main()
