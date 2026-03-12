#!/usr/bin/env python3
"""
publish_post.py — Auto-publishes draft posts and generates social content.
Runs daily. Takes the oldest draft, publishes it, triggers write_social.py.
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import subprocess
from datetime import datetime, timezone
from utils.common import get_logger, get_supabase, log_run, now_utc

logger = get_logger("publish_post")

def main():
    logger.info("=== Veltrix Publish Pipeline Starting ===")
    supabase = get_supabase()

    # Get oldest draft
    result = supabase.table("posts").select("*").eq("status", "draft").order("created_at", ascending=True).limit(1).execute()
    if not result.data:
        logger.info("No drafts to publish.")
        log_run(supabase, "publish_post", "skipped", "No drafts available", 0)
        return

    post = result.data[0]
    logger.info(f"Publishing: '{post['title']}'")

    # Update status to published
    supabase.table("posts").update({
        "status": "published",
        "published_at": now_utc(),
    }).eq("id", post["id"]).execute()

    logger.info(f"Published post ID {post['id']}: {post['title']}")

    # Trigger social script
    social_script = os.path.join(os.path.dirname(__file__), "write_social.py")
    subprocess.run([sys.executable, social_script, "--post-id", str(post["id"])], check=False)

    log_run(supabase, "publish_post", "success", f"Published: {post['title']}", 1)
    print(f"::notice title=Post Published::{post['title']}")

if __name__ == "__main__":
    main()
