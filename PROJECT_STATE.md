# Veltrix Collective — Project State
> **Last updated:** 2026-03-16
> Single source of truth. Read this at the start of every session before touching anything.

---

## 1. Services & Credentials

| Service | Purpose | Status | Key Details |
|---|---|---|---|
| **Hetzner VPS** | Discord bot (Agent 4) | Live | IP: 5.161.89.154 |
| **Vercel** | Next.js frontend | Live | Auto-deploys from GitHub main |
| **Namecheap** | Domain | Live | veltrixcollective.com → Vercel |
| **Supabase** | Primary database | Live | ID: qftpohuyvshbvhwxmkvn, ap-southeast-1 |
| **OpenAI** | Primary AI | Active | gpt-4o (quality) / gpt-4o-mini (cheap) |
| **Anthropic** | Fallback AI | Active | claude-sonnet-4-6 / claude-haiku-4-5-20251001 |
| **Brevo** | Email + newsletters | Live | hello@veltrixcollective.com sender |
| **Zoho** | Support inbox | Live | hello@veltrixcollective.com |
| **Lemon Squeezy** | Payments | Set up | Webhook → /api/activate-member |
| **Discord** | Community | Live | Bot: Veltrix#8512, Hetzner VPS |
| **Twitter/X** | @Veltrix_C posting | **LIVE** | Via Composio. First thread posted 2026-03-16. |
| **GitHub** | Repo + CI/CD | Live | Actions secrets in repo Settings |

---

## 2. Composio

**MCP URL:** `https://backend.composio.dev/v3/mcp/c87e99ef-e4a5-4294-808b-58afb31531d7/mcp?user_id=pg-test-cab455b4-3482-4a0e-a206-e14fda773ff5`
**Entity ID:** `pg-test-cab455b4-3482-4a0e-a206-e14fda773ff5`
**COMPOSIO_API_KEY:** in GitHub Actions secrets

**Connected accounts (active):**
- GitHub ✅
- Supabase ×2 ✅
- Twitter (@Veltrix_C) ✅ — connected 2026-03-16

### Twitter developer app — DO NOT CHANGE THESE SETTINGS
- App name: `2032611033354055680VeltrixBot`
- **App type: Web App, Automated App or Bot** (Confidential client) ← must stay this
- **Permissions: Read and Write** ← must stay this
- Callback URL: `https://backend.composio.dev/api/v1/auth-apps/add`
- Credits: paid/active as of 2026-03-16

### Composio REST API — VERIFIED WORKING (2026-03-16)
```
POST https://backend.composio.dev/api/v2/actions/TWITTER_CREATION_OF_A_POST/execute
Headers: x-api-key: {COMPOSIO_API_KEY}, Content-Type: application/json
Body: {
  "appName": "twitter",
  "entityId": "pg-test-cab455b4-3482-4a0e-a206-e14fda773ff5",
  "input": {"text": "...", "reply_in_reply_to_tweet_id": "..."}
}
Response: {"successfull": true, "data": {"data": {"id": "tweet_id"}}}
```

### Endpoint history (do not use these)
- `/api/v1/actions/` — 410 Gone (deprecated)
- `/api/v3/tools/` — 404 (wrong path)
- `/api/v3/actions/` — 404 (wrong path)
- `/api/v2/actions/` + `entityId: "default"` — 400 (wrong entity)
- **`/api/v2/actions/` + correct entityId — ✅ WORKS**

### CRITICAL: Composio SDK is broken — never use it
The `composio` Python package's `tools.execute()` breaks every version.
`requirements.txt` must only contain: `openai`, `anthropic`, `requests`.
Always call the REST API directly.

---

## 3. GitHub Actions Secrets

| Secret name | Python key | Purpose |
|---|---|---|
| NEXT_PUBLIC_SUPABASE_URL | os.environ["SUPABASE_URL"] | Supabase URL |
| SUPABASE_SERVICE_ROLE_KEY | os.environ["SUPABASE_SERVICE_KEY"] | Supabase writes |
| ANTHROPIC_API_KEY | os.environ["ANTHROPIC_API_KEY"] | Claude fallback |
| OPENAI_API_KEY | os.environ["OPENAI_API_KEY"] | OpenAI primary |
| BREVO_API_KEY | os.environ["BREVO_API_KEY"] | Brevo email |
| LEMON_SQUEEZY_API_KEY | os.environ["LEMON_SQUEEZY_API_KEY"] | Payments |
| LEMON_SQUEEZY_WEBHOOK_SECRET | os.environ["LEMON_SQUEEZY_WEBHOOK_SECRET"] | Webhook verify |
| COMPOSIO_API_KEY | os.environ["COMPOSIO_API_KEY"] | Composio REST API |

### Standard .yml env block
```yaml
env:
  SUPABASE_URL:                 ${{ secrets.NEXT_PUBLIC_SUPABASE_URL }}
  SUPABASE_SERVICE_KEY:         ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
  ANTHROPIC_API_KEY:            ${{ secrets.ANTHROPIC_API_KEY }}
  OPENAI_API_KEY:               ${{ secrets.OPENAI_API_KEY }}
  COMPOSIO_API_KEY:             ${{ secrets.COMPOSIO_API_KEY }}
```

### Standard AI call (OpenAI primary, Claude fallback)
```python
import openai, anthropic, logging, os
log = logging.getLogger(__name__)

def call_ai(prompt: str, max_tokens: int = 1000, quality: bool = False) -> str:
    openai_model    = "gpt-4o"            if quality else "gpt-4o-mini"
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

## 4. Supabase

**Project ID:** qftpohuyvshbvhwxmkvn | **Region:** ap-southeast-1 | **Postgres:** 17.6

**RLS:** All tables enabled.
- Public INSERT: `users` (anon signup)
- Public READ: `news`, `posts` (published only), `tools`, `llm_rankings`, `tool_comparisons`, `products`, `faq_items`, `newsletters`
- Public INSERT: `tool_votes`
- Private: `automation_logs`, `discord_logs`, `goal_checkins`, `referrals`, `social_posts`, `support_logs`

---

## 5. Agent Pipeline

| Agent | Status | Script | Trigger |
|---|---|---|---|
| **Agent 1: Scout** | ✅ LIVE | automations/news/scout.py | Every 3h (scout.yml) |
| **Agent 2: Writer** | ✅ LIVE | automations/content/write_post.py | Daily 2am UTC (daily.yml) |
| **Agent 3: Publisher** | ✅ LIVE | automations/content/publish_post.py | Daily 5am UTC (daily.yml) |
| **Agent 4: Discord Bot** | ✅ LIVE | Hetzner VPS | Continuous WebSocket |

### Manual dispatch (daily.yml)
- `run_writer: true` — triggers Writer only
- `run_publisher: true` — triggers Publisher only

### Publisher — exact working code
```python
COMPOSIO_ENTITY = "pg-test-cab455b4-3482-4a0e-a206-e14fda773ff5"

def post_tweet(text, reply_to_id=None):
    tool_input = {"text": text}
    if reply_to_id:
        tool_input["reply_in_reply_to_tweet_id"] = reply_to_id
    resp = requests.post(
        "https://backend.composio.dev/api/v2/actions/TWITTER_CREATION_OF_A_POST/execute",
        headers={"x-api-key": COMPOSIO_KEY, "Content-Type": "application/json"},
        json={"appName": "twitter", "entityId": COMPOSIO_ENTITY, "input": tool_input},
    )
    data = resp.json()
    if not data.get("successfull"):
        raise RuntimeError(f"Tweet failed: {data.get('error')}")
    return data["data"]["data"]["id"]
```

---

## 6. Site

4-step signup: `site/app/subscribe/page.tsx` + `site/app/api/subscribe/route.js`
Writes to `users` table, syncs to Brevo.

---

## 7. Repo Structure

```
veltrix-collective/
├── site/
│   ├── app/subscribe/page.tsx           LIVE
│   └── app/api/subscribe/route.js       LIVE
├── automations/
│   ├── news/scout.py                    LIVE (Agent 1)
│   └── content/
│       ├── write_post.py                LIVE (Agent 2)
│       ├── publish_post.py              LIVE (Agent 3)
│       └── requirements.txt             openai, anthropic, requests ONLY
├── .github/workflows/
│   ├── scout.yml                        Every 3h
│   └── daily.yml                        Writer 2am + Publisher 5am UTC
└── PROJECT_STATE.md                     This file
```

---

## 8. Known Gotchas

1. **Composio SDK is unusable** — use REST API only, never add `composio` to requirements.txt.
2. **Composio entity ID is NOT "default"** — must use `pg-test-cab455b4-3482-4a0e-a206-e14fda773ff5`.
3. **Composio endpoint:** `/api/v2/actions/{slug}/execute` with `appName` + `entityId` in body.
4. **Twitter app type must stay "Web App, Automated App or Bot"** — Native App breaks write access.
5. **Composio MCP requires full restart** after any Connected Account change.
6. **daily.yml manual dispatch:** use `run_publisher: true` to trigger Publisher only.
7. **Re-running a failed job** uses old commit code — always dispatch fresh for latest fixes.
8. **Twitter credits reset monthly** — current plan paid/active.
