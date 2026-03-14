"""
Publisher - Agent 3 for Veltrix Collective
Finds oldest draft post, publishes it, generates social captions,
posts to X if keys present, sends LinkedIn caption to Luke via Telegram with preview image.
Triggered daily at 3am UTC via GitHub Actions (1h after Writer).
"""

import os, re, logging, requests, io, base64
from datetime import datetime, timezone
import openai, anthropic
from supabase import create_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("publisher")

SUPABASE_URL  = os.environ["SUPABASE_URL"]
SUPABASE_KEY  = os.environ["SUPABASE_SERVICE_KEY"]
OPENAI_KEY    = os.environ["OPENAI_API_KEY"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
SITE_URL      = "https://veltrixcollective.com"

# X Keys - optional
X_API_KEY      = os.environ.get("X_API_KEY", "")
X_API_SECRET   = os.environ.get("X_API_SECRET", "")
X_ACCESS_TOKEN = os.environ.get("X_ACCESS_TOKEN", "")
X_ACCESS_SECRET = os.environ.get("X_ACCESS_SECRET", "")

# Telegram
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT