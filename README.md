# Veltrix Collective — Setup Guide

> **"You need AI to keep up with AI"**
> Full infrastructure for veltrixcollective.com — built to run 95%+ automated with zero PC dependency.

---

## Architecture Overview

| Layer | Tool | What it does |
|---|---|---|
| Frontend | Next.js 14 on Vercel | Website + all API routes |
| Database | Supabase (free) | Users, tools, posts, news, rankings |
| Automation | GitHub Actions (public repo = free) | All cron jobs |
| AI Brain | Claude API (Anthropic) | Content, news summaries, rankings, support |
| Email | Brevo | Newsletter + transactional emails |
| Payments | Lemon Squeezy | Insider Access paywall |
| LLM Tester | OpenRouter | Non-Claude models in the LLM Tester tool |

**PC independence:** Everything runs on GitHub Actions + Vercel + Supabase. If your computer explodes, the site keeps running.

---

## Step 1 — Accounts to Create (Do This First)

### 1.1 — GitHub (public repo)
1. Create a new **public** repo named `veltrix-collective`
2. Push this code: `git init && git add . && git commit -m "init" && git remote add origin https://github.com/YOUR_USERNAME/veltrix-collective.git && git push -u origin main`

> **Why public?** GitHub Actions is free for unlimited minutes on public repos. With hourly crons, you'd exceed the free tier on a private repo within days.

### 1.2 — Supabase
1. Go to [supabase.com](https://supabase.com) → New Project
2. Name it `veltrix-collective`, choose a region close to you
3. Go to **Project Settings → API** and copy:
   - **Project URL** → `SUPABASE_URL`
   - **anon public key** → `SUPABASE_ANON_KEY`
   - **service_role secret** → `SUPABASE_SERVICE_KEY`
4. Go to **SQL Editor** → paste the entire contents of `supabase/schema.sql` → Run
5. Also run these helper functions:
```sql
-- Vote counter
create or replace function increment_tool_votes(p_tool_id integer)
returns void as $$
  update tools set votes = votes + 1 where id = p_tool_id;
$$ language sql;

-- Referral counter
create or replace function increment_referral_count(referrer_code text)
returns void as $$
  update users set referral_count = referral_count + 1 where referral_code = referrer_code;
$$ language sql;
```

### 1.3 — Anthropic API
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. API Keys → Create new key
3. Copy → `ANTHROPIC_API_KEY`
4. Add $20 credit to start (covers ~1 month of automation)

### 1.4 — Brevo (email)
1. Go to [brevo.com](https://brevo.com) → Free account
2. **API Keys** (in your profile) → Generate API key → `BREVO_API_KEY`
3. Create **6 contact lists**:
   - `free-subscribers` → note the ID → `BREVO_FREE_LIST_ID`
   - `lifetime-members` → note the ID → `BREVO_LIFETIME_LIST_ID`
   - `tool-users`
   - `goal-setters`
   - `referrers`
   - `at-risk`
4. In **Senders** settings, verify `veltix@veltrixcollective.com` as a sender (requires DNS record — Brevo will guide you)

### 1.5 — Lemon Squeezy
1. Go to [lemonsqueezy.com](https://lemonsqueezy.com) → Create account
2. **Products → New Product:**
   - Name: `Veltrix Insider Access — Lifetime`
   - Price: $9.99 (create a variant with customer limit of 100)
   - Second variant: $19.99 (no limit)
   - Checkout copy: *"Join the first 100 insiders. Unlock Veltrix's full playbooks, deep-dive guides, and Discord access. One payment. Forever."*
3. **API → Generate key** → `LEMON_SQUEEZY_API_KEY`
4. Note your **Store ID** → `LEMON_SQUEEZY_STORE_ID`
5. **Webhooks → Add endpoint:**
   - URL: `https://www.veltrixcollective.com/api/activate-member`
   - Events: `order_created`
   - Copy the signing secret → `LEMON_SQUEEZY_WEBHOOK_SECRET`
6. Copy the checkout URL for your product → `NEXT_PUBLIC_LEMON_SQUEEZY_CHECKOUT_URL`
7. In product settings, enable **automatic refunds within 7 days**

### 1.6 — OpenRouter (for LLM Tester)
1. Go to [openrouter.ai](https://openrouter.ai) → Create account
2. API Keys → Create key → `OPENROUTER_API_KEY`
3. Add $5 credit (this will last months at low volume)

### 1.7 — Vercel
1. Go to [vercel.com](https://vercel.com) → Import your GitHub repo
2. Set **Root Directory** to `site`
3. Add all environment variables (listed in Step 3 below)
4. Deploy

### 1.8 — Cloudflare + Domain
You have `veltrixcollective.com` registered. To point it to Vercel via Cloudflare:

1. In **Cloudflare DNS**, add these records:
   ```
   Type: CNAME   Name: www    Value: cname.vercel-dns.com   Proxy: ON (orange cloud)
   Type: CNAME   Name: @      Value: cname.vercel-dns.com   Proxy: ON
   ```
2. In **Vercel project settings → Domains**, add `www.veltrixcollective.com` and `veltrixcollective.com`
3. Vercel will auto-provision SSL
4. In **Cloudflare → Caching → Configuration**:
   - Cache Level: Standard
   - Browser Cache TTL: 4 hours
5. Add Cloudflare Page Rule: `veltrixcollective.com/*` → Always use HTTPS

### 1.9 — Discord
1. Create server: `Veltrix Collective`
2. Create channels: `#ai-news`, `#tool-reviews`, `#build-in-public`, `#guides-discussion`, `#wins`
3. **Server Settings → Invites** — create a permanent invite link
4. Set this as `DISCORD_INVITE_URL` in your env vars

   > Note: For single-use invite links (more secure), generate them via Discord API. The current setup uses one permanent invite — upgrade later.

---

## Step 2 — GitHub Actions Secrets

Go to your GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**

Add ALL of these:

| Secret Name | Where to find it |
|---|---|
| `SUPABASE_URL` | Supabase Project Settings → API |
| `SUPABASE_SERVICE_KEY` | Supabase Project Settings → API (service_role) |
| `ANTHROPIC_API_KEY` | console.anthropic.com |
| `BREVO_API_KEY` | Brevo account settings |
| `BREVO_FREE_LIST_ID` | Brevo → Contacts → Lists (the number in the URL) |
| `BREVO_LIFETIME_LIST_ID` | Brevo → Contacts → Lists |
| `LEMON_SQUEEZY_API_KEY` | Lemon Squeezy API settings |
| `LEMON_SQUEEZY_STORE_ID` | Lemon Squeezy → Settings → Store |
| `OPENROUTER_API_KEY` | openrouter.ai |
| `OWNER_EMAIL` | lukejmadden@outlook.com (your email for reports) |
| `TWITTER_API_KEY` | Twitter Developer Portal (optional) |
| `TWITTER_API_SECRET` | Twitter Developer Portal (optional) |
| `TWITTER_ACCESS_TOKEN` | Twitter Developer Portal (optional) |
| `TWITTER_ACCESS_SECRET` | Twitter Developer Portal (optional) |

---

## Step 3 — Vercel Environment Variables

Go to Vercel → Project → Settings → Environment Variables. Add:

| Variable | Value |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Your Supabase URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Your Supabase anon key |
| `SUPABASE_SERVICE_KEY` | Your Supabase service role key |
| `ANTHROPIC_API_KEY` | Your Anthropic key |
| `OPENROUTER_API_KEY` | Your OpenRouter key |
| `BREVO_API_KEY` | Your Brevo key |
| `LEMON_SQUEEZY_API_KEY` | Your Lemon Squeezy key |
| `LEMON_SQUEEZY_WEBHOOK_SECRET` | Your webhook signing secret |
| `NEXT_PUBLIC_LEMON_SQUEEZY_CHECKOUT_URL` | Your checkout page URL |
| `DISCORD_INVITE_URL` | Your Discord invite link |
| `NEXT_PUBLIC_BASE_URL` | `https://www.veltrixcollective.com` |

---

## Step 4 — Seed Content (Do Before Going Live)

Before the automation kicks in, add 5 manual seed posts. Run this once locally:

```bash
cd automations
pip install -r requirements.txt

# Set your env vars locally first (copy .env.example to .env and fill it in)
python content/write_post.py  # Run 5 times — one post per run
```

Or write them manually via the Supabase table editor. Use these titles:
1. "Top 10 Claude Tools You Need in 2025 — Ranked by Veltrix"
2. "Best LLMs Right Now: GPT-4o vs Claude vs Gemini — Live Rankings"
3. "10 AI Tools for Freelancers That Actually Save Time"
4. "The AI News You Missed This Week — Veltrix Weekly Digest #1"
5. "Why Most People Are Using AI Wrong (And What Veltrix Uses Instead)"

Set `status = 'published'` and `published_at = now()` for all 5.

---

## Step 5 — Verify Everything is Running

After completing all steps above:

1. **Site loads:** Visit `https://www.veltrixcollective.com`
2. **News feed works:** Check `/news` — should show items
3. **Tools rankings work:** Check `/tools` — should show 30 seeded tools
4. **Subscribe works:** Try subscribing with a test email
5. **GitHub Actions running:** Go to your repo → Actions tab → check that `Hourly Automation` has run

To test a script manually: Go to GitHub Actions → select any workflow → Run workflow (manual trigger)

---

## Automation Schedule

| Script | Frequency | What it does |
|---|---|---|
| `fetch_news.py` | Hourly | Pulls 7 RSS feeds, summarises new items in Veltrix voice |
| `write_post.py` | Daily 2am | Finds trending AI topics, writes 1,200-word post |
| `publish_post.py` | Daily 2am | Publishes oldest draft, triggers social posting |
| `update_rankings.py` | Sunday 3am | Re-scores all tools + LLMs, generates movers post |
| `weekly_report.py` | Monday 7am | Sends you a 10-minute performance digest |
| `send_newsletter.py` | Tuesday 8am | Sends weekly digest to free + lifetime lists |
| `send_goal_checkins.py` | Wednesday 9am | Checks in on subscriber goals at 7/30/90-day marks |
| `check_referrals.py` | Thursday 10am | Awards referral milestones, upgrades gold referrers |
| `triage_support.py` | Daily 2am | Processes support emails, auto-resolves what it can |
| `update_content.py` | 1st of month | Rewrites low-traffic posts, generates SEO comparison pages |

---

## Your Weekly Time Commitment (~45 min)

| Task | Time |
|---|---|
| Read Monday performance report | 10 min |
| Review flagged support tickets in Supabase | 15 min |
| Check Discord for unanswered questions | 10 min |
| Approve/discard any draft posts if desired | 10 min |

Everything else runs itself.

---

## Revenue Timeline

| Month | Est. Revenue |
|---|---|
| 1-2 | $0–$50 |
| 3 | $100–$300 |
| 4-5 | $300–$800 |
| 6-8 | $500–$2,000 |
| 9-12 | $2,000–$5,000 |

Break-even: ~Month 3-4. First $1k month: ~Month 6-7.

---

*Built by AI. Curated by Veltix. Owned by you.*
