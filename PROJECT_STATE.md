# Veltrix Collective - Project State
> Last updated: 2026-03-15

## 0. Operating Rules
1. Discuss first, build second. Align with Luke before writing code. Counter-propose, stress-test ideas. Be a thinking partner.
2. Research before recommending. Check docs before suggesting solutions.
3. Automate blockers permanently. Build permanent solutions, document as How-To, never leave manual steps as recurring dependencies.
4. Secrets never in chat. Use Vercel env vars or Supabase vault. See Section 9 How-Tos.
5. Document every hard-won solution in Section 9 How-To guides.
6. Update PROJECT_STATE.md at end of every session via github-file-syncer inline mode (How-To #1).

## 1. Services
Hetzner VPS: Discord bot Agent 4, IP 5.161.89.154
Vercel: Next.js frontend, auto-deploys from GitHub main
Namecheap: veltrixcollective.com domain
OpenAI: PRIMARY AI (gpt-4o / gpt-4o-mini)
Anthropic: FALLBACK AI (claude-sonnet-4-6 / claude-haiku-4-5-20251001)
Supabase: Primary DB, Project ID qftpohuyvshbvhwxmkvn, ap-southeast-1
Brevo: Email + newsletters
Zoho: hello@veltrixcollective.com
Lemon Squeezy: Paywall, webhook to /api/activate-member
Discord: Veltrix#8512, posts news every 6h, Hetzner VPS
GitHub: Repo + CI/CD, Actions secrets in Settings

## 2. GitHub Actions Secrets
ANTHROPIC_API_KEY -> os.environ[ANTHROPIC_API_KEY]
OPENAI_API_KEY -> os.environ[OPENAI_API_KEY]
BREVO_API_KEY -> os.environ[BREVO_API_KEY]
LEMON_SQUEEZY_API_KEY -> os.environ[LEMON_SQUEEZY_API_KEY]
LEMON_SQUEEZY_WEBHOOK_SECRET -> os.environ[LEMON_SQUEEZY_WEBHOOK_SECRET]
NEXT_PUBLIC_SUPABASE_URL -> os.environ[SUPABASE_URL]
SUPABASE_SERVICE_ROLE_KEY -> os.environ[SUPABASE_SERVICE_KEY]

Standard yml env block uses: secrets.NEXT_PUBLIC_SUPABASE_URL, secrets.SUPABASE_SERVICE_ROLE_KEY, secrets.ANTHROPIC_API_KEY, secrets.OPENAI_API_KEY, secrets.BREVO_API_KEY, secrets.LEMON_SQUEEZY_API_KEY, secrets.LEMON_SQUEEZY_WEBHOOK_SECRET
Standard AI call: OpenAI primary (gpt-4o/gpt-4o-mini), Claude fallback (claude-sonnet-4-6/claude-haiku-4-5-20251001)

## 3. Supabase
Project ID: qftpohuyvshbvhwxmkvn | Region: ap-southeast-1 | Postgres: 17.6
RLS: Private (no policy): automation_logs, discord_logs, goal_checkins, referrals, social_posts, support_logs
RLS: Public READ: news, posts (published), tools, llm_rankings, tool_comparisons, products, faq_items, newsletters
RLS: Public INSERT: tool_votes
DB Functions: increment_tool_votes, increment_referral_count, get_github_token() SECURITY DEFINER
Edge Functions:
  github-file-syncer (v5) - DUAL MODE: inline {file_path,file_content,commit_message} OR github_file_queue. CORS enabled. PRIMARY deploy mechanism.
  github-pusher - deprecated
  run-github-sync - trigger wrapper
Vault secrets: GITHUB_TOKEN, VERCEL_TOKEN

Key schemas:
news: id, headline, summary, source_url, source_name, category, relevance_score, published_at, url_hash, post_id(FK->posts nullable)
posts: id, title, slug, content, excerpt, status, category, tags[], meta_title, meta_description, og_image_url, is_paywalled, view_count, published_at
social_posts: id, post_id(FK->posts), platform(twitter/linkedin/instagram), content, status(draft/published/failed), platform_post_id
github_file_queue: id, file_path, file_content(base64), commit_message, status(pending/synced/error), error_message, created_at, synced_at
users: id(uuid), email, tier(free/lifetime/pro), discord_invited, referral_code, segment, tags[], goal, onboarding_complete

## 4. Agent Pipeline
Agent 1 Scout: LIVE | automations/news/scout.py | Every 3h | RSS+Reddit+HN, OpenAI scoring, threshold 65, cap 30/run
Agent 2 Writer: LIVE | automations/content/write_post.py | Daily 2am UTC | score>=75, last 48h, gpt-4o, full HTML SEO post, published, sets news.post_id
Agent 3 Publisher: NOT BUILT | automations/content/publish_post.py | Daily 2am UTC after Writer | Discuss with Luke before building - need API creds
Agent 4 Discord Bot: LIVE | Hetzner VPS | Continuous WebSocket | Veltrix#8512, news every 6h
Agent 5 Monitor: NOT BUILT | automations/monitor/weekly_report.py | Monday 7am UTC

## 5. Workflows
scout.yml: cron 0 */3 * * * -> scout.py
daily.yml: cron 0 2 * * * -> write_post.py (+ publish_post.py when built)
(planned) weekly.yml: 0 8 * * 2
(planned) monitor.yml: 0 7 * * 1

## 6. Build Plan
Phase 1 Foundation: DONE
Phase 2 Content engine: PARTIAL (Scout+Writer live, Publisher not built)
Phase 3 Live rankings: TODO
Phase 4 Paywall & community: TODO
Phase 5 Tool portfolio: TODO
Phase 6 Support automation: TODO
Phase 7 Email & newsletter: TODO
Phase 8 Digital products: TODO
Phase 9 SEO & growth: TODO
Phase 10 Monitoring: TODO

## 7. Veltix Brand Voice
Persona: Veltix behind Veltrix Collective (veltrixcollective.com)
Voice: Authoritative but approachable. First person plural: we track, we tested, our rankings.
Tone: Slightly irreverent. Never corporate. Never hype. Specific.
Tagline: weave in naturally: you need AI to keep up with AI
Avoid: exclamation marks, vague statements, In todays fast-paced world, claiming to be human/Claude
Always end: CTA to a Veltrix tool or insider paywall

## 8. AI Models
gpt-4o-mini: OpenAI, scoring/classification/short summaries, PRIMARY cheap
gpt-4o: OpenAI, blog posts/newsletters/content, PRIMARY quality
claude-haiku-4-5-20251001: Anthropic, scoring/short summaries, FALLBACK cheap
claude-sonnet-4-6: Anthropic, blog posts/newsletters/content, FALLBACK quality

## 9. How-To Guides

### How-To #1: Pushing files to GitHub from a Claude session
Problem: Claude bash has no outbound network. GitHub PAT must never appear in chat.
Solution: github-file-syncer edge function - dual mode.

INLINE MODE (preferred for large/one-off files):
Run via Claude in Chrome javascript_tool on the veltrixcollective.com tab:
(async function() {
  var c = 'your file content here';
  var b = btoa(unescape(encodeURIComponent(c)));
  var r = await fetch('https://qftpohuyvshbvhwxmkvn.supabase.co/functions/v1/github-file-syncer', {
    method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({file_path:'path/file.md', file_content:b, commit_message:'[tag] message'})
  });
  return await r.text();
}())

QUEUE MODE (for multiple files or binary):
1. base64 encode: python3 -c "import base64; print(base64.b64encode(open('f','rb').read()).decode())"
2. INSERT INTO github_file_queue (file_path, file_content, commit_message, status) VALUES (..., 'pending')
3. Trigger: call edge function with body {} from browser using same javascript_tool pattern

Notes: edge fn fetches GITHUB_TOKEN from vault via get_github_token() RPC - no token in request ever
btoa(unescape(encodeURIComponent(content))) handles UTF-8 correctly in browser

### How-To #2: Accessing secrets from Supabase vault in edge functions
Problem: Need secrets without hardcoding or passing in requests.
Solution: Vault + SECURITY DEFINER SQL function + RPC call.

Step 1 - Create accessor (Supabase:apply_migration):
CREATE OR REPLACE FUNCTION get_my_secret() RETURNS text LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$ SELECT decrypted_secret FROM vault.decrypted_secrets WHERE name = 'MY_SECRET' LIMIT 1; $$;

Step 2 - Call from edge function:
const r = await fetch(supabaseUrl+'/rest/v1/rpc/get_my_secret', {method:'POST', headers:{apikey:serviceKey, Authorization:'Bearer '+serviceKey, 'Content-Type':'application/json'}, body:'{}'});
const secret = await r.json(); // returns string directly

Existing: GITHUB_TOKEN (get_github_token()), VERCEL_TOKEN
Gotchas: vault.decrypted_secrets NOT via JS .from() - RPC only. pg_net NOT installed. vault_decrypted_secret() built-in does NOT exist.

### How-To #3: Calling a Supabase Edge Function from a Claude session
Problem: Claude bash has no outbound network.
Solution: javascript_tool on veltrixcollective.com tab.

(async function() {
  var r = await fetch('https://qftpohuyvshbvhwxmkvn.supabase.co/functions/v1/YOUR-FN', {
    method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'
  });
  return await r.text();
}())

Requirements: edge fn MUST have CORS headers. Deploy with verify_jwt:false. Wrap in async IIFE. Use veltrixcollective.com tab (not newtab).

*Veltrix Collective - Built by AI. Curated by Veltix. Owned by you.*