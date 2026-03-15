# Veltrix Collective — Project State
> **Last updated:** 2026-03-16
> This file is the single source of truth for the project. Update it every time a new agent, script, integration, or schema change is deployed. Any AI session can read this file to get full context before building anything.

---

## 0. AI Session Rules (Read First)

These rules govern how every AI session must behave. Non-negotiable.

### Before starting any build
1. Read this full file
2. Do not ask Luke to confirm information already documented here
3. Use exact variable names, secret names, and model strings documented here — never invent alternatives

### Alignment before build
- For any task larger than a single-file fix, **discuss with Luke before writing a single line of code**
- Don't just agree — push back, propose alternatives, identify risks, stress-test the approach
- Ask: "Is this the right solution or just the obvious one?"
- If Luke's idea has a better alternative, say so with reasoning

### Automation first
- If a task requires Luke's manual input, first ask: "Can this be permanently automated?"
- Design the automation, propose it to Luke, get sign-off, then build it
- Only fall back to manual if there is genuinely no automation path

### Secrets rule
- **Never ask for or post secrets in chat**
- Secrets live in: GitHub Actions secrets (for workflow scripts) or Vercel env vars (for site)
- Secrets accessed programmatically via: Supabase vault → `get_github_token()` RPC pattern
- New secrets needed: add to GitHub Actions + Vercel dashboard, document name here, access via env
- See How-To #2

### Pushing to GitHub (from a session)
- Files <10KB: INSERT into `github_file_queue` → call `github-file-syncer` edge function
- Files >10KB (e.g. PROJECT_STATE.md): call `github-push-file` edge function directly from browser JS
- Never spend more than 2 tool calls trying an approach — if it fails, use the queue pattern
- See How-To #1

### Updating PROJECT_STATE.md
- Update at end of every session where a milestone was completed, script built, schema changed, or service added
- Use `github-push-file` edge function (large file) called from browser JS tab
- Commit message format: `[milestone] Brief description`

### Autonomy tiers (from dashboard)
- **FULLY AUTONOMOUS**: SEO updates, adding tools, social posts, metrics logging, running sales within limits, Scout
- **APPROVE THEN RUN**: A/B tests, new content angles, newsletter outreach, new cron jobs, journey posts
- **APPROVE BEFORE + AFTER**: Feature builds, pricing changes, payment flow, architecture changes

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
| **Composio** | Social API middleware (X, Zoho, Facebook) | PENDING SETUP | Luke connecting X + Zoho. Add COMPOSIO_API_KEY to GitHub secrets + Supabase vault when done |

### Database
| Service | Purpose | Status | Key Details |
|---|---|---|---|
| **Supabase** | Primary database | Live | Project ID: qftpohuyvshbvhwxmkvn, Region: ap-southeast-1 |

### Email
| Service | Purpose | Status | Key Details |
|---|---|---|---|
| **Brevo** | Transactional email + newsletters | Set up | Lists, sequences, API configured. List ID 2 = main newsletter list |
| **Zoho** | Custom inbox | Live | hello@veltrixcollective.com — connecting via Composio |

### Payments
| Service | Purpose | Status | Key Details |
|---|---|---|---|
| **Lemon Squeezy** | Paywall + subscriptions | Set up | Webhook to /api/activate-member |

### Community & Social
| Service | Purpose | Status | Key Details |
|---|---|---|---|
| **Discord** | Community hub | Live | Bot: Veltrix#8512. Posts news every 6h. Auto-restarts on Hetzner VPS. |
| **Telegram** | Content delivery to Luke + users | Live | Bot: @VeltrixPublisherV2_bot. Used for: LinkedIn drafts to Luke, lukejmadden@outlook.com alerts |
| **X/Twitter** | Social posting | PENDING | Free dev app needed at developer.x.com. Connect via Composio. |
| **Facebook** | Social posting | PENDING | Luke creating Veltrix Collective Page. Connect via Composio/Graph API. |

### Source Control
| Service | Purpose | Status | Key Details |
|---|---|---|---|
| **GitHub** | Repo + CI/CD | Live | Actions secrets in Settings -> Secrets -> Actions |

---