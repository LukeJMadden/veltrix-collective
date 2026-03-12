#!/usr/bin/env python3
"""
check_referrals.py — Veltrix Referral Rewards Engine
Weekly. Counts referrals per user, awards rewards at milestones,
sends reward emails automatically.
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from datetime import datetime, timezone
from utils.common import get_logger, get_supabase, get_anthropic, log_run, send_brevo_email

logger = get_logger("check_referrals")

REWARD_TIERS = {
    3: {"tier": "bronze", "reward": "exclusive guide unlock", "guide": "Referral Bonus: Building Your First AI Side Project"},
    10: {"tier": "silver", "reward": "3 months free Pro tool access"},
    25: {"tier": "gold", "reward": "lifetime Insider upgrade (if not already)"},
}

def award_reward(supabase, client, user: dict, milestone: int, reward_info: dict):
    """Send a reward email and update user record."""
    email_content = f"""
<div style="max-width:520px;margin:0 auto;font-family:Inter,sans-serif;color:#fff;background:#080b0f;padding:32px;border-radius:12px;border:1px solid #1e2733;">
  <span style="font-size:18px;font-weight:800;">Veltrix<span style="color:#00c2ff;">.</span></span>
  <div style="margin:24px 0;padding:16px;background:rgba(0,230,118,0.1);border:1px solid rgba(0,230,118,0.2);border-radius:8px;">
    <p style="color:#00e676;font-weight:600;margin:0;">🎉 You've hit {milestone} referrals</p>
  </div>
  <p style="color:#8b9ab0;font-size:15px;line-height:1.6;">
    {milestone} people subscribed to Veltrix through your link. That earns you: <strong style="color:#fff;">{reward_info['reward']}</strong>.
  </p>
  <p style="color:#8b9ab0;font-size:14px;margin-top:16px;">
    Keep sharing — next milestone unlocks even more. Your link:<br>
    <a href="https://www.veltrixcollective.com/subscribe?ref={user.get('referral_code','')}" style="color:#00c2ff;">
      https://www.veltrixcollective.com/subscribe?ref={user.get('referral_code','')}
    </a>
  </p>
  <p style="color:#4a5568;font-size:11px;margin-top:32px;">— Veltix · Veltrix Collective</p>
</div>"""

    send_brevo_email(user["email"], f"You earned a Veltrix reward — {milestone} referrals!", email_content)

    # Log referral reward
    supabase.table("referrals").insert({
        "referrer_code": user.get("referral_code", ""),
        "status": "rewarded",
        "reward_type": reward_info["tier"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }).execute()

    # If gold tier — upgrade to lifetime
    if reward_info["tier"] == "gold" and user.get("tier") != "lifetime":
        supabase.table("users").update({"tier": "lifetime", "referral_reward_tier": "gold"}).eq("id", user["id"]).execute()
        logger.info(f"  Upgraded {user['email']} to lifetime (gold referral reward)")
    else:
        supabase.table("users").update({"referral_reward_tier": reward_info["tier"]}).eq("id", user["id"]).execute()

def main():
    logger.info("=== Veltrix Referral Check Starting ===")
    supabase = get_supabase()
    client = get_anthropic()

    users = supabase.table("users").select("*").gt("referral_count", 0).execute().data
    logger.info(f"Found {len(users)} users with referrals")

    rewarded = 0
    for user in users:
        count = user.get("referral_count", 0)
        current_tier = user.get("referral_reward_tier", "none")

        for milestone, reward_info in sorted(REWARD_TIERS.items()):
            if count >= milestone and current_tier != reward_info["tier"] and current_tier not in [t["tier"] for m, t in REWARD_TIERS.items() if m > milestone]:
                logger.info(f"  {user['email']}: {count} referrals — awarding {reward_info['tier']}")
                try:
                    award_reward(supabase, client, user, milestone, reward_info)
                    rewarded += 1
                except Exception as e:
                    logger.warning(f"  Reward failed for {user['email']}: {e}")
                break

    logger.info(f"Awarded rewards to {rewarded} users.")
    log_run(supabase, "check_referrals", "success", f"Rewarded {rewarded} users", rewarded)

if __name__ == "__main__":
    main()
