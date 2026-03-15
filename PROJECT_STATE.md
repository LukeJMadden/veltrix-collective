# Veltrix Collective — Project State
> **Last updated:** 2026-03-15
> This file is the single source of truth for the project. Update it every time a new agent, script, integration, or schema change is deployed. Any AI session can read this file to get full context before building anything.

---

## 1. Services & Credentials

### Hosting & Infrastructure
| Service | Purpose | Status | Key Details |
|---|---|---|---|
| **Hetzner VPS** | Discord bot (Agent 4) — persistent process | Live | IP: 5.161.89.154 |
| **Vercel** | Next.js frontend | Live | Auto-deploys from GitHub main. Env vars in Vercel dashboard. |
| **Namecheap** | Domain registrar | Live | veltrixcollective.com — DNS points to Vercel |
| **Tailscale** | VPN | Not in use | Set up for separate project. Not needed for Veltrix. |

### AI & APIs
| Service | Purpose | Status | Key Details |
|---|---|---|---|
| **OpenAI** | PRIMARY AI — all writing, content, scoring | Active | Use until ~$100 credits exhausted |
| **Anthropic (Claude)** | FALLBACK AI | Active | Fallback when OpenAI unavailable |

### Database
| Service | Purpose | Status | Key Details |
|---|---|---|---|
| **Supabase** | Primary database | Live | Project ID: qftpohuyvshbvhwxmkvn, Region: ap-southeast-1 |

### Email
| Service | Purpose | Status | Key Details |
|---|---|---|---|
| **Brevo** | Transactional email + newsletters | Set up | Lists, sequences, API configured |
| **Zoho** | Custom inbox | Live | hello@veltrixcollective.com — support inbox + Brevo sender address |

### Payments
| Service | Purpose | Status | Key Details |
|---|---|---|---|
| **Lemon Squeezy** | Paywall + subscriptions | Set up | Webhook to /api/activate-member — updates users.tier + triggers Discord invite |

### Community
| Service | Purpose | Status | Key Details |
|---|---|---|---|
| **Discord** | Community hub | Live | Bot: Veltrix#8512. Posts news every 6h. Auto-restarts on Hetzner VPS. |

### Source Control
| Service | Purpose | Status | Key Details |
|---|---|---|---|
| **GitHub** | Repo + CI/CD | Live | Actions secrets in Settings -> Secrets -> Actions |

---

## 2. Environment Variables

### Vercel Dashboard
| Variable | Purpose |
|---|---|
| NEXT_PUBLIC_SUPABASE_URL | Supabase URL (public) |
| NEXT_PUBLIC_SUPABASE_ANON_KEY | Supabase anon key (frontend, RLS enforced) |
| SUPABASE_ANON_KEY | Supabase anon key (server-side API routes) |
| SUPABASE_SERVICE_KEY | Supabase service role key (server-side ONLY — bypasses RLS) |
| ANTHROPIC_API_KEY | Claude API (fallback) |
| OPENAI_API_KEY | OpenAI API (primary) |
| BREVO_API_KEY | Brevo email |
| LEMON_SQUEEZY_API_KEY | Lemon Squeezy |
| LEMON_SQUEEZY_STORE_ID | Lemon Squeezy store ID |
| LEMON_SQUEEZY_WEBHOOK_SECRET | Webhook verification |
| NEXT_PUBLIC_LEMON_SQUEEZY_CHECKOUT_URL | Checkout URL for frontend |
| DISCORD_INVITE_URL | Sent to users on purchase |
| NEXT_PUBLIC_SITE_URL | https://veltrixcollective.com |

### GitHub Actions Secrets
> IMPORTANT: These names differ slightly from Vercel. Always use exact names below in .yml files.

| Secret Name | Python env key | Purpose |
|---|---|---|
| ANTHROPIC_API_KEY | os.environ["ANTHROPIC_API_KEY"] | Claude fallback |
| OPENAI_API_KEY | os.environ["OPENAI_API_KEY"] | OpenAI primary |
| BREVO_API_KEY | os.environ["BREVO_API_KEY"] | Brevo email |
| LEMON_SQUEEZY_API_KEY | os.environ["LEMON_SQUEEZY_API_KEY"] | Lemon Squeezy |
| LEMON_SQUEEZY_WEBHOOK_SECRET | os.environ["LEMON_SQUEEZY_WEBHOOK_SECRET"] | Webhook verify |
| NEXT_PUBLIC_SUPABASE_URL | os.environ["SUPABASE_URL"] | Supabase URL |
| SUPABASE_SERVICE_ROLE_KEY | os.environ["SUPABASE_SERVICE_KEY"] | Supabase writes |

### Standard .yml env block (copy into every workflow)
```yaml
env:
  SUPABASE_URL:                 ${{ secrets.NEXT_PUBLIC_SUPABASE_URL }}
  SUPABASE_SERVICE_KEY:         ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
  ANTHROPIC_API_KEY:            ${{ secrets.ANTHROPIC_API_KEY }}
  OPENAI_API_KEY:               ${{ secrets.OPENAI_API_KEY }}
  BREVO_API_KEY:                ${{ secrets.BREVO_API_KEY }}
  LEMON_SQUEEZY_API_KEY:        ${{ secrets.LEMON_SQUEEZY_API_KEY }}
  LEMON_SQUEEZY_WEBHOOK_SECRET: ${{ secrets.LEMON_SQUEEZY_WEBHOOK_SECRET }}
```

### Standard Python env reads (copy into every script)
```python
import os
SUPABASE_URL  = os.environ["SUPABASE_URL"]
SUPABASE_KEY  = os.environ["SUPABASE_SERVICE_KEY"]
OPENAI_KEY    = os.environ["OPENAI_API_KEY"]
ANTHROPIC_KEY = os.environ["ANTHROPIC_API_KEY"]
BREVO_KEY     = os.environ["BREVO_API_KEY"]
LS_API_KEY    = os.environ["LEMON_SQUEEZY_API_KEY"]
```

### Standard AI call pattern — OpenAI PRIMARY, Claude FALLBACK
```python
import openai, anthropic, logging
log = logging.getLogger(__name__)

def call_ai(prompt: str, max_tokens: int = 1000, quality: bool = False) -> str:
    openai_model    = "gpt-4o"           if quality else "gpt-4o-mini"
    anthropic_model = "claude-sonnet-4-6" if quality else "claude-haiku-4-5-20251001"
    try:
        client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        resp = client.chat.completions.create(
            model=openai_model, max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content
    except Exception as e:
        log.warning(f"OpenAI failed ({e}), falling back to Anthropic")
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        msg = client.messages.create(
            model=anthropic_model, max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text
```

---

## 3. Supabase

**Project ID:** qftpohuyvshbvhwxmkvn  
**Region:** ap-southeast-1  
**DB Host:** db.qftpohuyvshbvhwxmkvn.supabase.co  
**Postgres:** 17.6

**RLS:** All tables enabled.  
Private (no policy = locked): automation_logs, discord_logs, goal_checkins, referrals, social_posts, support_logs  
Public READ: news, posts (published only), tools, llm_rankings, tool_comparisons, products, faq_items, newsletters  
Public INSERT: tool_votes

**DB Functions (all hardened with SET search_path = public):**
- increment_tool_votes(p_tool_id integer)
- increment_referral_count(referrer_code text)
- get_github_token() — reads GITHUB_TOKEN from vault.decrypted_secrets (SECURITY DEFINER)

**Supabase Edge Functions:**
- github-file-syncer — reads github_file_queue (pending rows), pushes to GitHub via vault token, marks synced. Call to deploy any file to GitHub repo. Has CORS headers.
- github-pusher — accepts files + token directly in request body (older version, prefer github-file-syncer)
- run-github-sync — one-shot trigger wrapper for github-file-syncer

---

## 4. Table Schemas

### users
id (uuid PK), email (unique), tier (free/lifetime/pro), discord_invited, discord_username, lemon_squeezy_order_id, referral_code (auto 8-char unique), referred_by, referral_count, referral_reward_tier, last_active, email_open_count, email_click_count, tool_usage_count, page_view_count, segment, tags[], goal, goal_check_count, last_goal_check, lead_magnet_delivered, lead_magnet_version, onboarding_step, onboarding_complete, created_at

### news
id (serial PK), headline, summary (Veltix-voice 3-sentence), source_url, source_name, category (default: ai-general), relevance_score (0-100), published_at, created_at, url_hash (unique 12-char SHA256 for dedup), post_id (FK->posts nullable — set when story has been written into a post)

### posts
id, title, slug (unique), content, excerpt, status (draft/published), category, tags[], meta_title, meta_description, og_image_url, is_paywalled, view_count, published_at, created_at, updated_at

### social_posts
id, post_id (FK->posts), platform (twitter/linkedin/instagram), content, status (draft/published/failed), platform_post_id

### tools
id, name, slug (unique), url, category (claude-tools/llm/image/productivity/writing), description, score, votes, affiliate_url, is_veltrix_tool (Veltrix Pick badge), featured, logo_url, pricing_model (free/freemium/paid), monthly_price_usd, tags[], updated_at, created_at

### tool_votes
id, tool_id (FK->tools), ip_hash, user_id (FK->users nullable), voted_at

### llm_rankings
id, model_name, provider, slug (unique), score_overall/coding/reasoning/creativity/speed/cost_efficiency, context_window, input_cost_per_1m, output_cost_per_1m, api_url, affiliate_url, notes, updated_at

### products
id, title, slug (unique), description, price_usd, product_type (prompt-pack/guide/pdf), lemon_squeezy_product_id, gumroad_product_id, pdf_url, preview_url, sales_count, active

### newsletters
id, subject, content_html (free), content_premium_html (lifetime), status (draft/sent), recipient_count, open_count, click_count, sent_at

### referrals
id, referrer_code, referred_email, referred_user_id (FK->users), status (pending/confirmed), reward_type

### tool_comparisons
id, tool_a_id (FK->tools), tool_b_id (FK->tools), slug (unique e.g. chatgpt-vs-claude), content, meta_description, view_count

### faq_items
id, question, answer, times_asked, approved

### support_logs / discord_logs / automation_logs
Backend-only logging tables. No RLS policy. See Supabase for full columns.

### github_file_queue
id, file_path, file_content (base64), commit_message, status (pending/synced/error), error_message, created_at, synced_at
**Usage:** INSERT rows here, then call github-file-syncer edge function to push to repo.

---

## 5. Agent Pipeline

| Agent | Status | Script | Trigger | Notes |
|---|---|---|---|---|
| Agent 1: Scout | LIVE | automations/news/scout.py | Every 3h (GitHub Actions) | RSS + Reddit RSS + HN. Scores with OpenAI. Saves to news table. |
| Agent 2: Writer | LIVE | automations/content/write_post.py | Daily 2am UTC (daily.yml) | Picks top unwritten story (score>=75, last 48h), writes full SEO post in Veltix voice, saves to posts as published. Marks news.post_id. |
| Agent 3: Publisher | NOT BUILT | automations/content/publish_post.py | On new published post | Posts directly to social APIs — no Buffer needed |
| Agent 4: Discord Bot | LIVE | Hetzner VPS | Continuous (WebSocket) | Veltrix#8512. Posts news every 6h. Auto-restarts. Must be always-on — that's why it's on VPS not Actions. |
| Agent 5: Monitor | NOT BUILT | automations/monitor/weekly_report.py | Monday 7am UTC | |

**Why Discord bot is on Hetzner and not GitHub Actions:**
Discord requires a persistent WebSocket connection (always-on). GitHub Actions runs a job and dies. All other agents are cron jobs (run, finish, stop) — perfect for Actions. Persistent process = VPS. Scheduled job = Actions.

### Scout detail
- Model: gpt-4o-mini (OpenAI primary) with claude-haiku-4-5-20251001 fallback
- Threshold: 65/100. Lookback: 4h. Cap: 30/run.
- Sources: TechCrunch AI, Verge AI, Anthropic Blog, OpenAI Blog, HuggingFace, MIT Tech Review, VentureBeat AI (RSS) + r/artificial, r/MachineLearning, r/ClaudeAI, r/ChatGPT, r/singularity, r/LLMDevs (Reddit RSS) + HN
- Reddit: uses /r/{sub}/new.rss (NOT JSON API — returns 403)
- Dedup: url_hash (SHA256 12-char)

### Writer detail
- Model: gpt-4o (quality=True) with claude-sonnet-4-6 fallback
- Threshold: relevance_score >= 75, last 48h, post_id IS NULL
- Output: full HTML blog post, SEO fields, published immediately
- Dedup: sets news.post_id after writing to prevent rewrites

---

## 6. GitHub Actions Workflows

| File | Cron | Runs |
|---|---|---|
| .github/workflows/scout.yml | 0 */3 * * * | automations/news/scout.py |
| .github/workflows/daily.yml | 0 2 * * * | Writer (+ Publisher when built) |
| (planned) weekly.yml | 0 8 * * 2 | Newsletter |
| (planned) monitor.yml | 0 7 * * 1 | Monitor report |

---

## 7. Repo Structure

```
veltrix-collective/
├── site/                          # Next.js (Vercel)
├── automations/
│   ├── news/
│   │   ├── scout.py               LIVE
│   │   └── requirements.txt
│   ├── content/
│   │   ├── write_post.py          LIVE
│   │   ├── publish_post.py        PLANNED
│   │   ├── write_social.py        PLANNED
│   │   └── requirements.txt       LIVE
│   ├── email/
│   │   ├── send_newsletter.py     PLANNED
│   │   └── send_goal_checkins.py  PLANNED
│   ├── rankings/
│   │   └── update_rankings.py     PLANNED
│   ├── support/
│   │   └── triage_support.py      PLANNED
│   └── monitor/
│       └── weekly_report.py       PLANNED
├── .github/workflows/
│   ├── scout.yml                  LIVE
│   ├── daily.yml                  LIVE
│   ├── weekly.yml                 PLANNED
│   └── monitor.yml                PLANNED
└── PROJECT_STATE.md               THIS FILE
```

---

## 8. AI Model Reference

| Model | Provider | Use for | Priority |
|---|---|---|---|
| gpt-4o-mini | OpenAI | Scoring, classification, short summaries | PRIMARY cheap |
| gpt-4o | OpenAI | Blog posts, newsletters, content | PRIMARY quality |
| claude-haiku-4-5-20251001 | Anthropic | Scoring, short summaries | FALLBACK cheap |
| claude-sonnet-4-6 | Anthropic | Blog posts, newsletters, content | FALLBACK quality |

---

## 9. Veltix Brand Voice

```
You are Veltix, the AI persona behind Veltrix Collective (veltrixcollective.com).
Voice: Authoritative but approachable. First person. "we track", "we tested", "our rankings".
Tone: Slightly irreverent. Never corporate. Never hype. Specific about what matters.
Tagline: Occasionally weave in "you need AI to keep up with AI" naturally.
Avoid: Excessive exclamation marks. Vague statements. "In todays fast-paced world". Claiming to be human or Claude.
Always end with a CTA to a Veltrix tool or the insider paywall.
```

---

## 10. Build Plan Status

| Phase | Status | Summary |
|---|---|---|
| Phase 1 - Foundation | DONE | VPS, Supabase, Vercel, repo, all services live |
| Phase 2 - Content engine | PARTIAL | Scout + Writer live; Publisher not built |
| Phase 3 - Live rankings | TODO | Tools leaderboard, LLM page |
| Phase 4 - Paywall & community | TODO | Lemon Squeezy set up; guides page + Discord roles not built |
| Phase 5 - Tool portfolio | TODO | Matchmaker, LLM Tester, News Summariser |
| Phase 6 - Support automation | TODO | Crisp chat, email triage |
| Phase 7 - Email & newsletter | TODO | Brevo set up; sequences + newsletter script not built |
| Phase 8 - Digital products | TODO | AI Video Prompt Pack + 4 others. Gumroad account ready. |
| Phase 9 - SEO & growth | TODO | Programmatic compare pages |
| Phase 10 - Monitoring | TODO | Weekly report script |

---

*Veltrix Collective - Built by AI. Curated by Veltix. Owned by you.*
