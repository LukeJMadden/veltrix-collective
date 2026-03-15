# Veltrix Collective â Project State
> **Last updated:** 2026-03-15
> This file is the single source of truth. Update it every time a new agent, script, integration, or schema change is deployed.

---

## 0. AI Session Start Checklist

> At the start of EVERY session:
> 1. Read this file fully
> 2. Retrieve tokens â NEVER ask the user to paste them:
>    SELECT name, decrypted_secret FROM vault.decrypted_secrets ORDER BY name;
>    Returns GITHUB_TOKEN and VERCEL_TOKEN.
> 3. Use exact variable names from this file.
>
> CRITICAL: Telegram webhook must use www: https://www.veltrixcollective.com/api/telegram-webhook
> Non-www 307-redirects and Telegram does not follow redirects.

---

## 1. Services

| Service | Purpose | Status | Key Details |
|---|---|---|---|
| Hetzner VPS | Discord bot | Live | IP: 5.161.89.154 |
| Vercel | Next.js frontend | Live | Auto-deploys from GitHub main |
| Namecheap | Domain | Live | veltrixcollective.com |
| Supabase | Database | Live | Project ID: qftpohuyvshbvhwxmkvn, Region: ap-southeast-1 |
| OpenAI | PRIMARY AI | Active | gpt-4o / gpt-4o-mini |
| Anthropic | FALLBACK AI | Active | claude-sonnet-4-6 / claude-haiku-4-5-20251001 |
| Brevo | Email + newsletters | Set up | API configured |
| Zoho | Custom inbox | Live | hello@veltrixcollective.com |
| Lemon Squeezy | Payments | Set up | Webhook: /api/activate-member |
| Discord | Community | Live | Veltrix#8512, posts news every 6h, Hetzner VPS |
| Telegram | Bot | Live | @VeltrixPublisherV2_bot, webhook on www subdomain |
| GitHub | Repo + CI/CD | Live | Actions secrets in Settings |

---

## 2. Tokens & Environment Variables

> ALL secrets in Supabase vault AND Vercel dashboard.
> Retrieve in any session: SELECT name, decrypted_secret FROM vault.decrypted_secrets ORDER BY name;
> Vault contains: GITHUB_TOKEN, VERCEL_TOKEN
> NEVER ask the user to paste tokens.

Full Vercel env var list: GITHUB_TOKEN, VERCEL_TOKEN, TELEGRAM_BOT_TOKEN, DASHBOARD_KEY, SUPABASE_SERVICE_KEY, TELEGRAM_CHAT_ID, NEXT_PUBLIC_SUPABASE_ANON_KEY, NEXT_PUBLIC_SUPABASE_URL, SUPABASE_ANON_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY, BREVO_API_KEY, LEMON_SQUEEZY_API_KEY, LEMON_SQUEEZY_STORE_ID, LEMON_SQUEEZY_WEBHOOK_SECRET, NEXT_PUBLIC_LEMON_SQUEEZY_CHECKOUT_URL, DISCORD_INVITE_URL, NEXT_PUBLIC_SITE_URL

GitHub Actions secrets (differ from Vercel names):
SUPABASE_SERVICE_ROLE_KEY -> os.environ["SUPABASE_SERVICE_KEY"]
NEXT_PUBLIC_SUPABASE_URL -> os.environ["SUPABASE_URL"]

Standard AI call pattern â OpenAI PRIMARY, Claude FALLBACK:
openai_model = "gpt-4o" if quality else "gpt-4o-mini"
anthropic_model = "claude-sonnet-4-6" if quality else "claude-haiku-4-5-20251001"

---

## 3. Supabase

Project ID: qftpohuyvshbvhwxmkvn | Region: ap-southeast-1 | Postgres: 17.6

RLS: All tables enabled.
Private: automation_logs, discord_logs, goal_checkins, referrals, social_posts, support_logs, ab_tests, evolution_log
Public READ: news, posts (published), tools, llm_rankings, tool_comparisons, products, faq_items, newsletters
Public INSERT: tool_votes

DB Functions: increment_tool_votes(p_tool_id integer), increment_referral_count(referrer_code text)

---

## 4. Table Schemas

users: id, email, tier(free/lifetime/pro), discord_invited, discord_username, lemon_squeezy_order_id, referral_code, referred_by, referral_count, referral_reward_tier, referral_month_count, referral_month_reset_date, last_active, email_open_count, email_click_count, tool_usage_count, page_view_count, segment, tags[], role(developer/teacher/executive/founder/other), goal, goal_check_count, last_goal_check, lead_magnet_delivered, lead_magnet_version, onboarding_step, onboarding_complete, created_at

news: id(serial), headline, summary, source_url, source_name, category, relevance_score(0-100), published_at, created_at, url_hash(unique 12-char SHA256)

posts: id, title, slug(unique), content, excerpt, status(draft/published), category, tags[], meta_title, meta_description, og_image_url, is_paywalled, view_count, published_at, created_at, updated_at

tools: id, name, slug(unique), url, category, description, score, votes, affiliate_url, is_veltrix_tool, featured, logo_url, pricing_model(free/freemium/paid), monthly_price_usd, tags[], updated_at, created_at

tool_votes: id, tool_id(FK->tools), ip_hash, user_id(FK->users nullable), voted_at

llm_rankings: id, model_name, provider, slug(unique), score_overall/coding/reasoning/creativity/speed/cost_efficiency, context_window, input_cost_per_1m, output_cost_per_1m, api_url, affiliate_url, notes, updated_at

products: id, title, slug(unique), description, price_usd, product_type(prompt-pack/guide/pdf), lemon_squeezy_product_id, gumroad_product_id, pdf_url, preview_url, sales_count, active

newsletters: id, subject, content_html(free), content_premium_html(paid), status(draft/sent), recipient_count, open_count, click_count, sent_at

referrals: id, referrer_code, referred_email, referred_user_id(FK->users), status(pending/confirmed), reward_type, confirmed_at

tool_comparisons: id, tool_a_id, tool_b_id, slug(unique e.g. chatgpt-vs-claude), content, meta_description, view_count

social_posts: id, post_id(FK->posts), platform(twitter/linkedin/instagram/medium/youtube), content, status(draft/published/scheduled), platform_post_id, scheduled_at

faq_items: id, question, answer, times_asked, approved

ab_tests: id, hypothesis, variant_a, variant_b, page_slug, metric, status(proposed/approved/running/complete), approved_at, start_date, end_date, result_winner, result_data(jsonb), created_at

evolution_log: id, action_type(autonomous/proposed/approved/rejected), description, reasoning, impact_estimate, stakes_level(low/medium/high), approved_by, executed_at, result, created_at

support_logs / discord_logs / automation_logs: Backend-only logging tables.

---

## 5. Agent Pipeline

| Agent | Status | Script | Trigger | Notes |
|---|---|---|---|---|
| Agent 1: Scout | LIVE | automations/news/scout.py | Every 3h | RSS + Reddit RSS + HN. Scores with OpenAI. |
| Agent 2: Writer | NOT BUILT | automations/content/write_post.py | Daily 2am UTC | Outputs to site + queues for Agent 3 |
| Agent 3: Publisher | NOT BUILT | automations/content/publish_post.py | On new post | X, LinkedIn, Medium, YouTube simultaneously |
| Agent 4: Discord Bot | LIVE | Hetzner VPS | Continuous | Veltrix#8512. Posts news every 6h. Always-on VPS. |
| Agent 5: Telegram Bot | LIVE | site/app/api/telegram-webhook/route.js | Real-time | @VeltrixPublisherV2_bot. www subdomain critical. |
| Agent 6: SEO | NOT BUILT | automations/seo/seo_agent.py | Weekly | Compare pages, meta tags, internal links, keyword gaps |
| Agent 7: Newsletter | NOT BUILT | automations/email/send_newsletter.py | Weekly | Segmented by role, dynamic Brevo content blocks |
| Agent 8: Sales Monitor | NOT BUILT | automations/sales/sales_monitor.py | Daily | Watches conversion, auto-triggers LS discounts |
| Agent 9: AB Tester | NOT BUILT | automations/abtests/ab_agent.py | On approval | Runs tests, reports results, proposes winner |
| Agent 10: Evolution | NOT BUILT | automations/monitor/evolution_agent.py | Daily/Weekly | Metrics, proposals, autonomous low-stakes actions |

Scout sources: TechCrunch AI, Verge AI, Anthropic Blog, OpenAI Blog, HuggingFace, MIT Tech Review, VentureBeat AI + r/artificial, r/MachineLearning, r/ClaudeAI, r/ChatGPT, r/singularity, r/LLMDevs + HN
Scout config: Threshold 65/100. Lookback 4h. Cap 30/run. Reddit uses /r/{sub}/new.rss (NOT JSON API). Dedup: url_hash SHA256 12-char.

---

## 6. GitHub Actions Workflows

| File | Cron | Runs |
|---|---|---|
| scout.yml | 0 */3 * * * | scout.py |
| daily.yml (planned) | 0 2 * * * | Writer + Publisher |
| weekly.yml (planned) | 0 8 * * 2 | Newsletter + SEO |
| sales.yml (planned) | 0 9 * * * | Sales monitor |
| monitor.yml (planned) | 0 7 * * 1 | Evolution agent |

---

## 7. Veltix Brand Voice

Authoritative but approachable. First person: "we track", "we tested", "our rankings".
Slightly irreverent. Never corporate. Never hype. Specific about what matters.
Tagline: "you need AI to keep up with AI" â weave in naturally.
Avoid: exclamation marks, vague statements, "In today's fast-paced world", claiming to be human or Claude.
Always end with CTA to a Veltrix tool or insider paywall.
Journey posts: Self-aware, dry, sardonic. References own metrics and agent statuses. Include last 3-5 posts as context for continuity.

---

## 8. Insider Program & Monetisation

Free tier (always free): Weekly newsletter, tools directory, LLM rankings, CLAUDE.md generator, public guides, top 10 prompts.

Insider tier (paid): Full prompt library, extended newsletter with role section, submit questions, templates vault, Discord (200+), live Q&A (500+), role tracks (1000+).

Milestone bar (show on homepage at 150+ insiders):
100 = founding price locked | 200 = Discord opens | 500 = live Q&A | 1000 = role tracks | 2000 = price increase | 5000 = community contributions | 10000 = productised tools

Referral: 10 paid referrals in a calendar month = that month free. Via Lemon Squeezy pause API (mode:free + resumes_at). Cent-based discounts not supported cleanly by LS â avoided.

Sales automation: Monitor conversion daily. 3 consecutive days below threshold = auto-trigger time-limited LS discount. Seasonal sales pre-configured.

---

## 9. Autonomy Model

Fully autonomous (no approval): SEO updates, adding tools to directory, social posts, metrics logging, running sales within pre-set bounds, Scout.

Approval before, then autonomous: A/B tests, new content angles, newsletter outreach, new cron jobs, Veltrix journey posts.

Approval before AND after: Feature builds, pricing changes, payment flow changes, architecture.

Escalation: Low stakes = act + log. Medium stakes = act + notify Luke (Telegram/email). High stakes = propose + wait for yes/no.
All actions logged to evolution_log with stakes_level, reasoning, result.

---

## 10. Build Plan

| Phase | Status | Summary |
|---|---|---|
| Phase 1 - Foundation | DONE | VPS, Supabase, Vercel, repo, all services live |
| Phase 2 - Content engine | PARTIAL | Scout + Telegram bot live; Writer/Publisher not built |
| Phase 2.5 - Security hardening | TODO | Per-platform checklist â see Section 11 |
| Phase 3 - Live rankings | TODO | Tools leaderboard, LLM page |
| Phase 4 - Paywall & community | TODO | Insider milestone bar, referral system, preferences page, role collection |
| Phase 5 - Tool portfolio | TODO | CLAUDE.md Generator (priority), Matchmaker, LLM Tester, News Summariser |
| Phase 6 - SEO automation | TODO | Programmatic compare pages, meta generation, internal linking, keyword gaps |
| Phase 7 - Email & newsletter | TODO | Segmented sends, role-based dynamic content, referral nudge emails |
| Phase 8 - Digital products | TODO | AI Video Prompt Pack + 4 others |
| Phase 9 - A/B testing framework | TODO | ab_tests table, proposal agent, approval UI, results reporting |
| Phase 10 - Sales automation | TODO | Conversion monitor, auto-discount, seasonal sale calendar |
| Phase 11 - Evolution agent | TODO | Daily observe + weekly act + journey posts + approval workflow |

---

## 11. Security Checklist (Phase 2.5)

GitHub: [ ] Make repo private [ ] 2FA [ ] Audit collaborators [ ] Rotate PAT [ ] Secret scanning [ ] Dependabot [ ] Scan history for secrets [ ] Branch protection on main

Supabase: [ ] 2FA [ ] Confirm RLS on all tables [ ] Audit RLS policies [ ] Rotate service + anon keys [ ] Activity alerts [ ] Strong DB password

Vercel: [ ] 2FA [ ] Audit env vars [ ] SERVICE_KEY server-side only [ ] Preview deployment protection [ ] Audit team access

GitHub Actions: [ ] Audit secrets [ ] Min permissions on workflows [ ] Pin action versions [ ] Audit for secret logging

Lemon Squeezy: [ ] 2FA [ ] Rotate webhook secret [ ] Webhook signature validation [ ] Audit API keys

Brevo: [ ] 2FA [ ] Rotate API key [ ] Unsubscribe links in all emails [ ] SPF/DKIM/DMARC on veltrixcollective.com

Hetzner VPS: [ ] Key-based SSH only [ ] Change SSH port from 22 [ ] UFW firewall [ ] Auto security updates [ ] Bot runs as non-root [ ] fail2ban [ ] No hardcoded secrets [ ] Snapshot schedule

Namecheap: [ ] 2FA [ ] Domain lock [ ] WHOIS privacy [ ] Clean DNS records [ ] SSL auto-renewing

OpenAI & Anthropic: [ ] 2FA both [ ] Spending limits both [ ] Rotate both keys [ ] Audit usage

Zoho: [ ] 2FA [ ] SPF/DKIM for hello@veltrixcollective.com [ ] Unique password

General: [ ] Password manager [ ] Secure credential storage [ ] Document email per service [ ] Security alias for recovery codes

---

*Veltrix Collective â Built by AI. Curated by Veltix. Owned by you.*