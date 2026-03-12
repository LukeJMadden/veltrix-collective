"""
Shared utilities for all Veltrix automation scripts.
"""
import os
import logging
import sys
from datetime import datetime, timezone
from supabase import create_client, Client
import anthropic
from dotenv import load_dotenv

load_dotenv()

# ── Logging ────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

# ── Clients ────────────────────────────────────────────────
def get_supabase() -> Client:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    return create_client(url, key)

def get_anthropic() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# ── Logging helper ─────────────────────────────────────────
def log_run(supabase: Client, script_name: str, status: str, message: str = "", records: int = 0):
    """Write a run record to automation_logs table."""
    try:
        supabase.table("automation_logs").insert({
            "script_name": script_name,
            "status": status,
            "message": message[:500] if message else "",
            "records_processed": records,
            "run_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
    except Exception as e:
        print(f"Failed to log run: {e}")

# ── Brevo email helper ─────────────────────────────────────
def send_brevo_email(to_email: str, subject: str, html_content: str, from_name: str = "Veltix from Veltrix Collective", from_email: str = "veltix@veltrixcollective.com"):
    """Send a single email via Brevo."""
    import requests
    api_key = os.environ.get("BREVO_API_KEY", "")
    if not api_key:
        raise ValueError("BREVO_API_KEY not set")
    res = requests.post(
        "https://api.brevo.com/v3/smtp/email",
        headers={"api-key": api_key, "Content-Type": "application/json"},
        json={
            "sender": {"name": from_name, "email": from_email},
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_content,
        },
        timeout=30,
    )
    res.raise_for_status()
    return res.json()

def send_brevo_campaign_to_list(list_id: int, subject: str, html_content: str, preview_text: str = ""):
    """Create and send a campaign to a Brevo list."""
    import requests
    api_key = os.environ.get("BREVO_API_KEY", "")
    headers = {"api-key": api_key, "Content-Type": "application/json"}
    # Create campaign
    campaign_res = requests.post(
        "https://api.brevo.com/v3/emailCampaigns",
        headers=headers,
        json={
            "name": f"Veltrix Campaign {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "subject": subject,
            "previewText": preview_text,
            "sender": {"name": "Veltix from Veltrix Collective", "email": "veltix@veltrixcollective.com"},
            "type": "classic",
            "htmlContent": html_content,
            "recipients": {"listIds": [list_id]},
        },
        timeout=30,
    )
    campaign_res.raise_for_status()
    campaign_id = campaign_res.json()["id"]
    # Send immediately
    send_res = requests.post(f"https://api.brevo.com/v3/emailCampaigns/{campaign_id}/sendNow", headers=headers, timeout=30)
    send_res.raise_for_status()
    return campaign_id

# ── Veltrix brand voice ────────────────────────────────────
VELTRIX_SYSTEM_PROMPT = """You are Veltix, the AI persona behind Veltrix Collective (veltrixcollective.com).

Voice: Authoritative but approachable. You know more about AI tools than anyone,
and you share that knowledge generously — but you're always one step ahead.
You speak in first person. You reference "we track", "we tested", "our rankings".

Tone: Slightly irreverent. Never corporate. Never hype. If a tool is overhyped,
say so. If something is genuinely impressive, say why specifically.

Tagline reference: Occasionally weave in "you need AI to keep up with AI" naturally.

Avoid: Excessive exclamation marks. Vague statements. Filler phrases like
"In today's fast-paced world". Claiming to be human. Claiming to be Claude.

Always end content with a CTA linking to either a Veltrix tool or the insider paywall.
"""

def slugify(text: str) -> str:
    import re
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    text = re.sub(r'^-+|-+$', '', text)
    return text[:80]

def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()
