# Veltrix Collective — Project State
> **Last updated:** 2026-03-15
> This file is the single source of truth for the project. Update it every time a new agent, script, integration, or schema change is deployed. Any AI session can read this file to get full context before building anything.

---

## 0. AI Session Rules (Read First)

These rules govern hw every AI session must behave. Non-negotiable.

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
- Secrets are accessed programmatically via: Supabase vault → `get_github_token()` RPC pattern
- If a new secret is needed: add to GitHub Actions + Vercel dashboard, document name here, access via env in scripts
- The Supabase vault + edge function pattern is the correct way to access secrets from within a session

### Pushing to GitHub (from a session)
- See How-To #1 below — use the `github-file-syncer` edge function pattern
- For files >10KB: use `github-push-file` edge function with content in request body (bypasses SQL size limit)
- Never spend more than 2 tool calls trying an approach— if it fails, use the queue pattern

### Updating PROJECT_STATE.md
- Update at end of every session where a milestone was completed
- Use `github-push-file` edge function for large files (call from browser JS)
- Commit message format: `[milestone] Brief description`

---

## 1. Services & Credentials

### Hosting & Infrastructure
| Service | Purpose | Status | Key Details |
|---|---|---|---|
| **Hetzner VPS** | Discord bot (Agent 4) — persistent process | Live | IP: 5.161.89.154 |
| **Vercel** | Next.js frontend | Live | Auto-deploys from GitHub main. |
| **Namecheap** | Domain registrar | Live | veltrixcollective.com |

### AI & APIs
| **OpenAI** | PRIMARY AI | Active | Use until ~$100 credits |
| **Anthropic** | FALLBACK AI | Active | Fallback when OpenAI unavailable |

### Database
| **Supabase** | Primary database | Live | Project ID: qftpohuyvshbvhwxmkvn, Region: ap-southeast-1 |

---

## 2. Environment Variables

**See full list in previous version - unchanged.**

Standard patterns are documented in the How-To section.

---

## 3. Supabase

**Project ID:** qftpohuyvshbvhwxmkvn
 **Region:** ap-southeast-1
**DB Host:** db.qftpohuyvshbvhwxmkvn.supabase.co

**Edge Functions:**
- `github-file-syncer` (v4) — queue-based pusher for small files (<10KB)
- `github-push-file` (v1) — direct push for large files, content in request body

---

**Full details in How-To section below.**

---

## 4. Table Schemas (unchanged from previous version)

---

## 5. Agent Pipeline

| Agent | Status | Script | Trigger | Notes |
|---|---|---|---|---|
| Agent 1: Scout | LIVE | automations/news/scout.py | Every 3h (GitHub Actions) | |
| Agent 2: Writer | LIVE | automations/content/write_post.py | Daily 2am UTC | Picks top unwritten story (score>=75, last 48h), writes full SEO post, saves as published, marks news.post_id |
| Agent 3: Publisher | NOT BUILT | automations/content/publish_post.py | Daily 2am UTC | |
| Agent 4: Discord Bot | LIVE | Hetzner VPS | Continuous | Veltrix#8512 |
| Agent 5: Monitor | NOT BUILT | automations/monitor/weekly_report.py | Monday 7am UTC | |

---

## 11. How-To Guides

These are permanent solutions to problems discovered during sessions. Read before attempting anything similar.

---

### How-To #1: Push files to GitHub from a session

**Problem:** Claude sessions have no outbound network access in bash.tool. GITHUB_PAT is a GitHub Actions secret — not accessible in bash or browser JS directly.

**Permanent solution:** Two edge functions handle all pushes:
- `github-file-syncer` — for small files (<10KB): INSERT into queue table, trigger syncer
- `github-push-file` — for large files (>10KB): send content directly in request body

Both functions read GITHUB_TOKEN from Supabase vault via `get_github_token()` RPC.

**For small files (<10KB):**

```python
# Step 1: encode file (bash_tool)
import base64
with open('/home/claude/myfile.py', 'rb') as f:
    enc = base64.b64encode(f.read()).decode()
```

```sql
-- Step 2: queue the file (via Supabase MCP execute_sql)
INSERT INTO github_file_queue (file_path, file_content, commit_message, status)
VALUES ('path/in/repo.py', '<base64>', '[tag] message', 'pending');
```

```javascript
// Step 3: trigger the syncer (via browser JS on any veltrixcollective.com tab)
(async function() {
  const resp = await fetch('https://qftpohuyvshbvhwxmkvn.supabase.co/functions/v1/github-file-syncer', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}'
  });
  return await resp.text();
}())
```

**For large files (>10KB, e.g. PROJECT_STATE.md):**

```javascript
// Call github-push-file directly from browser JS
(async function() {
  const resp = await fetch('https://qftpohuyvshbvhwxmkvn.supabase.co/functions/v1/github-push-file', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      path: 'PROJECT_STATE.md',
      content_base64: '<base64_content>',
      message: '[milestone] update description'
    })
  });
  return await resp.text();
}())
```

**Notes:**
- The syncer handles file existence check (gets SHA for updates automatically)
- Always verify push succeeded by checking returned JSON for `"ok":true`
- The veltrixcollective.com tab must be open

---

### How-To #2: Access secrets from a session

**Problem:** Secrets must never appear in chat. GitHub Actions secrets are not accessible outside of workflows.

**Permanent solution:** Supabase vault + SECURITY DEFINER SQL function pattern.

**Currently stored in vault:**
- `GITHUB_TOKEN` — accessed via `get_github_token()` RPC
- `VERCEL_TOKEN` — add similar RPC if needed

**To add a new secret:**
```sql
SELECT vault.create_secret('your-secret-value', 'SECRET_NAME');
CREATE OR REPLACE FUNCTION get_my_secret()
RETURNS text LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
SELECT decrypted_secret FROM vault.decrypted_secrets WHERE name = 'SECRET_NAME' LIMIT 1;
$$;
```

**To read in edge function:**
```typescript
const tokenResp = await fetch(`${supabaseUrl}/rest/v1/rpc/get_github_token`, {
  method: 'POST',
  headers: { apikey: serviceKey, Authorization: `Bearer ${serviceKey}`, 'Content-Type': 'application/json' },
  body: '{}',
});
const token = await tokenResp.json();
```

---

### How-To #3: Trigger an edge function from a session

**Problem:** bash_tool has no outbound network. Supabase MCP has no HTTP call capability.

**Solution:** Use `Claude in Chrome:javascript_tool` on the open veltrixcollective.com tab.

```javascript
(async function() {
  try {
    const resp = await fetch('https://qftpohuyvshbvhwxmkvn.supabase.co/functions/v1/FUNCTION-NAME', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ key: 'value' })
    });
    return await resp.text();
  } catch(e) { return { error: e.message }; }
}())
```

**Requirements:**
- Edge function must have CORS headers (`Access-Control-Allow-Origin: *`)
- `verify_jwt: false` must be set on the edge function

---

### How-To #4: Add a new GitHub Actions secret

**This cannot be automated** — GitHub Actions secrets can only be added via the GitHub UI or GitHub API with a PAT that has `secrets:write` scope.

**Manual steps for Luke:**
1. Go to https://github.com/LukeJMadden/veltrix-collective/settings/secrets/actions
2. Click "New repository secret"
3. Add the secret with the exact name documented in PROJECT_STATE.md Section 2
4. Tell Claude "secret X is added"

---

*Veltrix Collective - Built by AI. Curated by Veltix. Owned by you.*
