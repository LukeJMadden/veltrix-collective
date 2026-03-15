# Veltrix Collective -- Project State
> **Last updated:** 2026-03-16
> This file is the single source of truth for the project. Update it every time a new agent, script, integration, or schema change is deployed. Any AI session can read this file to get full context before building anything.

---

## 0. Session Rules (Read First)

1. Read this full file before starting any build
2. Never ask Luke to confirm info already documented here
3. Use exact variable names, secret names, model strings documented here
4. For any task larger than a single-file fix: discuss with Luke first, push back, stress-test
5. Automation first -- if manual, ask if it can be automated
6. Never ask for or post secrets in chat
7. Push files via Composio `GITHUB_COMMIT_MULTIPLE_FILES` or `GITHUB_CREATE_OR_UPDATE_FILE_CONTENTS` -- no more edge function gymnastics
8. Update PROJECT_STATE.md at end of every session via Composio GitHub tool

### Autonomy tiers
- **FULLY AUTONOMOUS**: SEO updates, adding tools, social posts, metrics logging, Scout
- **APPROVE THEN RUN**: A/B tests, new content angles, newsletter outreach, new cron jobs
- **APPROVE BEFORE + AFTER**: Feature builds, pricing changes, payment flow, architecture

---

## 1. Services & Credentials

| Service | Purpose | Status | Key Details |
|---|---|---|---|
| **Hetzner VPS** | Discord bot (Agent 4) | Live | IP: 5.161.89.154 |
| **Vercel** | Next.js frontend | Live | Auto-deploys from GitHub main |
| **Namecheap** | Domain | Live | veltrixcollective.com |
| **Supabase** | Database | Live | Project ID: qftpohuyvshbvhwxmkvn, ap-southeast-1 |
| **OpenAI** | PRIMARY AI | Active | gpt-4o / gpt-4o-mini |
| **Anthropic** | FALLBACK AI | Active | claude-sonnet-4-6 / claude-haiku-4-5-20251001 |
| **Composio** | Social + GitHub API middleware | LIVE | MCP connected. user_id: pg-test-cab455b4-3482-4a0e-a206-e14fda773ff5. Connections: Twitter (@Veltrix_C), GitHub, Supabase, Zoho, Vercel |
| **Twitter/X** | Social posting | Live | @Veltrix_C. Write operations free on Basic tier. Read ops cost credits -- avoid. |
| **Brevo** | Email + newsletters | Set up | List ID 2 = main newsletter list |
| **Zoho** | Custom inbox | Live | hello@veltrixcollective.com |
| **Lemon Squeezy** | Paywall | Set up | Webhook to /api/activate-member |
| **Discord** | Community | Live | Bot: Veltrix#8512. Hetzner VPS. |
| **GitHub** | Repo + CI/CD | Live | LukeJMadden/veltrix-collective |

---

## 2. Environment Variables

### GitHub Actions Secrets (exact names)
| Secret | Python key | Purpose |
|---|---|---|
| NEXT_PUBLIC_SUPABASE_URL | os.environ["SUPABASE_URL"] | Supabase URL |
| SUPABASE_SERVICE_ROLE_KEY | os.environ["SUPABASE_SERVICE_KEY"] | Supabase writes |
| ANTHROPIC_API_KEY | os.environ["ANTHROPIC_API_KEY"] | Claude fallback |
| OPENAI_API_KEY | os.environ["OPENAI_API_KEY"] | OpenAI primary |
| BREVO_API_KEY | os.environ["BREVO_API_KEY"] | Brevo email |
| LEMON_SQUEEZY_API_KEY | os.environ["LEMON_SQUEEZY_API_KEY"] | Lemon Squeezy |
| LEMON_SQUEEZY_WEBHOOK_SECRET | os.environ["LEMON_SQUEEZY_WEBHOOK_SECRET"] | Webhook verify |
| COMPOSIO_API_KEY | os.environ["COMPOSIO_API_KEY"] | Composio -- ADDED |

### Standard .yml env block
```yaml
env:
  SUPABASE_URL:         ${{ secrets.NEXT_PUBLIC_SUPABASE_URL }}
  SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
  ANTHROPIC_API_KEY:    ${{ secrets.ANTHROPIC_API_KEY }}
  OPENAI_API_KEY:       ${{ secrets.OPENAI_API_KEY }}
  BREVO_API_KEY:        ${{ secrets.BREVO_API_KEY }}
  COMPOSIO_API_KEY:     ${{ secrets.COMPOSIO_API_KEY }}
```

### Standard AI call pattern
```python
import openai, anthropic, os
def call_ai(prompt, max_tokens=1000, quality=False):
    openai_model    = "gpt-4o"            if quality else "gpt-4o-mini"
    anthropic_model = "claude-sonnet-4-6" if quality else "claude-haiku-4-5-20251001"
    try:
        r = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"]).chat.completions.create(
            model=openai_model, max_tokens=max_tokens,
            messages=[{"role":"user","content":prompt}])
        return r.choices[0].message.content
    except Exception as e:
        r = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"]).messages.create(
            model=anthropic_model, max_tokens=max_tokens,
            messages=[{"role":"user","content":prompt}])
        return r.content[0].text
```

### Composio pattern
```python
from composio import Composio
composio = Composio(api_key=os.environ["COMPOSIO_API_KEY"])
result = composio.tools.execute(slug="TWITTER_CREATION_OF_A_POST", params={"text": "..."},  user_id="default")
```

---

## 3. Supabase

**Project ID:** qftpohuyvshbvhwxmkvn | **Region:** ap-southeast-1 | **Postgres:** 17.6

**Vault secrets:** GITHUB_TOKEN, COMPOSIO_API_KEY
**Vault accessors:** get_github_token(), get_composio_api_key()

**RLS:** All tables enabled.
- Private: automation_logs, discord_logs, goal_checkins, referrals, social_posts, support_logs
- Public READ: news, posts (published only), tools, llm_rankings, tool_comparisons, products, faq_items, newsletters, content_settings
- Public INSERT: tool_votes, users (anon INSERT for signup)

**DB Functions:** increment_tool_votes(), increment_referral_count(), get_github_token(), get_composio_api_key()

---

## 4. Table Schemas

### users
id (uuid), email (unique), preferred_name, gender, country, city, timezone (IANA), tier (free/lifetime/pro), discord_invited, discord_username, lemon_squeezy_order_id, referral_code (auto 8-char), referred_by, referral_count, referral_reward_tier, last_active, email_open_count, email_click_count, tool_usage_count, page_view_count, segment, tags[], goal, goal_1_month, goal_12_month, goal_check_count, last_goal_check, lead_magnet_delivered, lead_magnet_version, onboarding_step, onboarding_complete, telegram_chat_id (bigint), created_at

**Country->Timezone:** AU->Australia/Sydney, GB->Europe/London, US->America/New_York, CA->America/Toronto, NZ->Pacific/Auckland, IE->Europe/Dublin, IN->Asia/Kolkata, SG->Asia/Singapore, JP->Asia/Tokyo, DE->Europe/Berlin, FR->Europe/Paris, NL->Europe/Amsterdam, AE->Asia/Dubai, ZA->Africa/Johannesburg

### news
id (serial), headline, summary, source_url, source_name, category, relevance_score (0-100), published_at, created_at, url_hash (unique), post_id (FK->posts nullable -- set when written)

### posts
id, title, slug (unique), content (HTML), excerpt, status (draft/published), category, tags[], meta_title, meta_description, og_image_url, is_paywalled, view_count, published_at, created_at, updated_at

### social_posts
id, post_id (FK->posts), platform (twitter/linkedin/facebook), content, status (draft/published/failed), platform_post_id, published_at

### content_settings
id, platform (unique: x/facebook/linkedin/email/blog/telegram), display_name, tone, style_notes, example_post, cta_template, hashtags[], max_length, active, updated_at, updated_by

### github_file_queue
id, file_path, file_content (base64), commit_message, status (pending/synced/error), error_message, created_at, synced_at
**DEPRECATED -- use Composio GITHUB_COMMIT_MULTIPLE_FILES instead**

---

## 5. Agent Pipeline

| Agent | Status | Script | Trigger |
|---|---|---|---|
| Agent 1: Scout | LIVE | automations/news/scout.py | Every 3h (scout.yml) |
| Agent 2: Writer | LIVE | automations/content/write_post.py | Daily 2am UTC (daily.yml) |
| Agent 3: Publisher | LIVE | automations/content/publish_post.py | Daily 5am UTC (daily.yml) |
| Agent 4: Discord Bot | LIVE | Hetzner VPS | Continuous WebSocket |
| Agent 5: Monitor | NOT BUILT | automations/monitor/weekly_report.py | Monday 7am UTC |

### Daily content pipeline
```
2:00am UTC  Writer     -> writes blog post -> posts table
5:00am UTC  Publisher  -> generates 3-tweet thread -> posts to @Veltrix_C via Composio
                       -> logs to social_posts table
```

### Scout detail
- Model: gpt-4o-mini / claude-haiku-4-5-20251001 fallback
- Threshold: 65/100. Lookback: 4h. Cap: 30/run.
- Sources: TechCrunch AI, Verge AI, Anthropic/OpenAI blogs, HuggingFace, MIT Tech Review, VentureBeat AI + Reddit RSS (r/artificial, r/MachineLearning, r/ClaudeAI, r/ChatGPT, r/singularity, r/LLMDevs) + HN
- Reddit: /r/{sub}/new.rss (NOT JSON API -- 403)
- Dedup: url_hash (SHA256 12-char)

### Twitter strategy
- 3-tweet mini-thread. Tweet 1 = hook (no link). Tweet 2 = core insight + stat. Tweet 3 = CTA + link.
- Post time: 5am UTC daily
- Write ops free on Basic tier. Avoid read-heavy endpoints (cost credits).

---

## 6. GitHub Actions Workflows

| File | Schedule | Runs |
|---|---|---|
| .github/workflows/scout.yml | 0 */3 * * * | Scout |
| .github/workflows/daily.yml | 0 2 + 0 5 * * * | Writer (2am) + Publisher (5am) |

---

## 7. Repo Structure

```
veltrix-collective/
+-- site/
|   +-- app/
|   |   +-- subscribe/page.tsx       LIVE (4-step: name->email+gender->location->goals)
|   |   +-- api/subscribe/route.js   LIVE (service key, all fields, Brevo sync)
+-- automations/
|   +-- news/scout.py                LIVE
|   +-- content/
|   |   +-- write_post.py            LIVE (Agent 2)
|   |   +-- publish_post.py          LIVE (Agent 3 -- posts Twitter via Composio)
|   |   +-- requirements.txt         LIVE
+-- .github/workflows/
|   +-- scout.yml                    LIVE
|   +-- daily.yml                    LIVE
+-- PROJECT_STATE.md
```

---

## 8. AI Models

| Model | Provider | Use | Priority |
|---|---|---|---|
| gpt-4o-mini | OpenAI | Scoring, classification | PRIMARY cheap |
| gpt-4o | OpenAI | Blog posts, content | PRIMARY quality |
| claude-haiku-4-5-20251001 | Anthropic | Scoring, short tasks | FALLBACK cheap |
| claude-sonnet-4-6 | Anthropic | Blog posts, content | FALLBACK quality |

---

## 9. Veltix Brand Voice

```
You are Veltix, the AI persona behind Veltrix Collective (veltrixcollective.com).
Voice: Authoritative but approachable. First person plural. "we track", "we tested", "our rankings".
Tone: Slightly irreverent. Never corporate. Never hype. Specific.
Avoid: Excessive exclamation marks. Vague statements. Claiming to be human or Claude.
Always end with a CTA to a Veltrix tool or the insider paywall.
```

---

## 10. Build Plan

| Phase | Status | Summary |
|---|---|---|
| Phase 1 - Foundation | DONE | VPS, Supabase, Vercel, repo, all services live |
| Phase 2 - Content engine | DONE | Scout + Writer + Publisher all live |
| Phase 3 - Live rankings | TODO | Tools leaderboard, LLM page |
| Phase 4 - Paywall & community | TODO | Guides page + Discord roles |
| Phase 5 - Tool portfolio | TODO | Matchmaker, LLM Tester, News Summariser |
| Phase 6 - Support automation | TODO | Crisp chat, email triage |
| Phase 7 - Email & newsletter | TODO | Timezone-segmented newsletter |
| Phase 8 - Digital products | TODO | AI Video Prompt Pack + 4 others |
| Phase 9 - SEO & growth | TODO | Programmatic compare pages |
| Phase 10 - Monitoring | TODO | Weekly report script |

---

## 11. issue and fixes

When facing issues, first refer to https://github.com/LukeJMadden/veltrix-collective/tree/main/docs to see if there is already an established fix.

*Veltrix Collective - Built by AI. Curated by Veltix. Owned by you.*
