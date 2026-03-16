# Veltrix Collective — Project State
> **Last updated:** 2026-03-16
> This file is the single source of truth for the project. Update it every time a new agent, script, integration, or schema change is deployed. Any AI session can read this file to get full context before building anything.

---

## 1. Services & Credentials

### Hosting & Infrastructure
| Service | Purpose | Status | Key Details |
|---|---|---|---|
| **Hetzner VPS** | Discord bot (Agent 4) — persistent process | Live | IP: 5.161.89.154 |
| **Vercel** | Next.js frontend | Live | Auto-deploys from GitHub main. Env vars in Vercel dashboard. |
| **Namecheap** | Domain registrar | Live | veltrixcollective.com — DNS points to Vercel |

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
| **Zoho** | Custom inbox | Live | hello@veltrixcollective.com |

### Payments
| Service | Purpose | Status | Key Details |
|---|---|---|---|
| **Lemon Squeezy** | Paywall + subscriptions | Set up | Webhook to /api/activate-member |

### Community
| Service | Purpose | Status | Key Details |
|---|---|---|---|
| **Discord** | Community hub | Live | Bot: Veltrix#8512. Posts news every 6h. Auto-restarts on Hetzner VPS. |

### Social
| Service | Purpose | Status | Key Details |
|---|---|---|---|
| **Twitter / X** | @Veltrix_C daily thread | LIVE | Connected via Composio. App type: Web App/Bot (Confidential client). Read+Write. |

### Source Control
| Service | Purpose | Status | Key Details |
|---|---|---|---|
| **GitHub** | Repo + CI/CD | Live | Actions secrets in Settings -> Secrets -> Actions |

---

## 2. Composio MCP

**MCP URL:** `https://backend.composio.dev/v3/mcp/c87e99ef-e4a5-4294-808b-58afb31531d7/mcp?user_id=pg-test-cab455b4-3482-4a0e-a206-e14fda773ff5`
**User ID:** `pg-test-cab455b4-3482-4a0e-a206-e14fda773ff5`
**Connected accounts:** GitHub, Supabase ×2, Twitter (@Veltrix_C) ✅
**COMPOSIO_API_KEY:** stored in GitHub Actions secrets

### Twitter app setup (IMPORTANT — do not change)
- App name: 2032611033354055680VeltrixBot
- App type: **Web App, Automated App or Bot** (Confidential client) ← must stay this way
- Permissions: **Read and Write**
- Callback URL: https://backend.composio.dev/api/v1/auth-apps/add
- Connected account: @Veltrix_C OAuth via Composio Connected Accounts

### Composio REST API (used by Publisher)
```
POST https://backend.composio.dev/api/v1/actions/TWITTER_CREATION_OF_A_POST/execute
Headers: x-api-key: {COMPOSIO_API_KEY}, Content-Type: application/json
Body: {"entityId": "default", "input": {"text": "...", "reply_in_reply_to_tweet_id": "..."}}
Response: {"successfull": true, "data": {"data": {"id": "tweet_id"}}}
```

---

## 3. Environment Variables

### GitHub Actions Secrets
| Secret Name | Python env key | Purpose |
|---|---|---|
| ANTHROPIC_API_KEY | os.environ["ANTHROPIC_API_KEY"] | Claude fallback |
| OPENAI_API_KEY | os.environ["OPENAI_API_KEY"] | OpenAI primary |
| BREVO_API_KEY | os.environ["BREVO_API_KEY"] | Brevo email |
| LEMON_SQUEEZY_API_KEY | os.environ["LEMON_SQUEEZY_API_KEY"] | Lemon Squeezy |
| LEMON_SQUEEZY_WEBHOOK_SECRET | os.environ["LEMON_SQUEEZY_WEBHOOK_SECRET"] | Webhook verify |
| NEXT_PUBLIC_SUPABASE_URL | os.environ["SUPABASE_URL"] | Supabase URL |
| SUPABASE_SERVICE_ROLE_KEY | os.environ["SUPABASE_SERVICE_KEY"] | Supabase writes |
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

### Standard AI call pattern — OpenAI PRIMARY, Claude FALLBACK
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

**Project ID:** qftpohuyvshbvhwxmkvn
**Region:** ap-southeast-1

**RLS:** All tables enabled.
Public INSERT: users (anon signup)
Public READ: news, posts (published only), tools, llm_rankings, tool_comparisons, products, faq_items, newsletters
Private: automation_logs, discord_logs, goal_checkins, referrals, social_posts, support_logs

---

## 5. Agent Pipeline

| Agent | Status | Script | Trigger | Notes |
|---|---|---|---|---|
| Agent 1: Scout | LIVE | automations/news/scout.py | Every 3h (scout.yml) | RSS + Reddit + HN. Scores with OpenAI. Saves to news table. |
| Agent 2: Writer | LIVE | automations/content/write_post.py | Daily 2am UTC (daily.yml) | Writes full SEO posts from top news. Saves to posts table. |
| Agent 3: Publisher | LIVE | automations/content/publish_post.py | Daily 5am UTC (daily.yml) | Generates 3-tweet thread via OpenAI. Posts via Composio v1 REST API. |
| Agent 4: Discord Bot | LIVE | Hetzner VPS | Continuous WebSocket | Posts news every 6h to Discord. |

### Publisher — verified working Composio call
```python
resp = requests.post(
    "https://backend.composio.dev/api/v1/actions/TWITTER_CREATION_OF_A_POST/execute",
    headers={"x-api-key": COMPOSIO_KEY, "Content-Type": "application/json"},
    json={"entityId": "default", "input": {"text": text, "reply_in_reply_to_tweet_id": reply_id}},
)
```

---

## 6. Repo Structure

```
veltrix-collective/
├── site/app/subscribe/page.tsx          LIVE (4-step signup)
├── site/app/api/subscribe/route.js      LIVE
├── automations/content/
│   ├── write_post.py                    LIVE (Agent 2)
│   ├── publish_post.py                  LIVE (Agent 3)
│   └── requirements.txt                 openai, anthropic, requests
├── automations/news/scout.py            LIVE (Agent 1)
├── .github/workflows/
│   ├── scout.yml                        LIVE (every 3h)
│   └── daily.yml                        LIVE (writer 2am + publisher 5am UTC)
└── PROJECT_STATE.md                     this file
```

---

## 7. Known Issues / Gotchas

- **Composio SDK unusable** — `tools.execute()` signature changes between versions. Always use the REST API directly (`/api/v1/actions/{slug}/execute`). Never use the composio Python package.
- **Twitter app type must stay as "Web App, Automated App or Bot"** — switching back to Native App breaks write access.
- **MCP session must be restarted** after changing Composio connected accounts.
- **requirements.txt** only needs: openai, anthropic, requests — no composio package.
