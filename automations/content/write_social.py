#!/usr/bin/env python3
"""
write_social.py — Generates social captions for a published post.
Called by publish_post.py. Posts to X and LinkedIn directly (no Buffer needed).
"""
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import argparse, json, requests
from utils.common import get_logger, get_supabase, get_anthropic, log_run, VELTRIX_SYSTEM_PROMPT

logger = get_logger("write_social")

def generate_captions(client, post: dict) -> dict:
    """Generate social captions for all platforms."""
    msg = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=800,
        system=VELTRIX_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"""Generate social media captions for this post.

Post title: {post['title']}
Post excerpt: {post.get('excerpt', '')[:200]}
Post URL: https://www.veltrixcollective.com/posts/{post['slug']}

Return a JSON object (no markdown, raw JSON only):
{{
  "twitter": ["caption 1 under 280 chars", "caption 2 under 280 chars", "caption 3 under 280 chars"],
  "linkedin": "200-word professional post in Veltrix voice. Start with a hook, not 'I'. End with the URL.",
  "instagram": "Caption with 5 relevant hashtags at the end.",
  "video_script": "60-second TTS-ready script in Veltrix voice. Punchy sentences. Built for ElevenLabs."
}}"""
        }]
    )
    text = msg.content[0].text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON
        import re
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
        return {"twitter": [], "linkedin": "", "instagram": "", "video_script": ""}

def post_to_twitter(captions: list[str]) -> bool:
    """Post to X/Twitter using API v2."""
    bearer = os.environ.get("TWITTER_BEARER_TOKEN")
    api_key = os.environ.get("TWITTER_API_KEY")
    api_secret = os.environ.get("TWITTER_API_SECRET")
    access_token = os.environ.get("TWITTER_ACCESS_TOKEN")
    access_secret = os.environ.get("TWITTER_ACCESS_SECRET")

    if not all([api_key, api_secret, access_token, access_secret]):
        logger.warning("Twitter credentials not configured — skipping")
        return False

    try:
        import requests
        from requests_oauthlib import OAuth1
        auth = OAuth1(api_key, api_secret, access_token, access_secret)
        caption = captions[0] if captions else ""
        if not caption:
            return False
        res = requests.post(
            "https://api.twitter.com/2/tweets",
            auth=auth,
            json={"text": caption},
            timeout=30,
        )
        if res.status_code == 201:
            logger.info("Posted to Twitter successfully")
            return True
        else:
            logger.warning(f"Twitter post failed: {res.status_code} {res.text[:200]}")
            return False
    except Exception as e:
        logger.warning(f"Twitter error: {e}")
        return False

def save_scripts(post_id: int, captions: dict, supabase):
    """Save video script and social content to DB / log."""
    if captions.get("video_script"):
        script_dir = os.path.join(os.path.dirname(__file__), "..", "..", "scripts")
        os.makedirs(script_dir, exist_ok=True)
        with open(os.path.join(script_dir, f"post_{post_id}_video.txt"), "w") as f:
            f.write(captions["video_script"])
        logger.info(f"Video script saved for post {post_id}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--post-id", type=int, required=True)
    args = parser.parse_args()

    supabase = get_supabase()
    client = get_anthropic()

    result = supabase.table("posts").select("*").eq("id", args.post_id).single().execute()
    if not result.data:
        logger.error(f"Post {args.post_id} not found")
        return

    post = result.data
    logger.info(f"Generating social content for: {post['title']}")

    captions = generate_captions(client, post)
    logger.info(f"Generated: {len(captions.get('twitter', []))} tweets, LinkedIn: {bool(captions.get('linkedin'))}")

    post_to_twitter(captions.get("twitter", []))
    save_scripts(args.post_id, captions, supabase)

    log_run(supabase, "write_social", "success", f"Post {args.post_id}: {post['title'][:50]}", 1)

if __name__ == "__main__":
    main()
