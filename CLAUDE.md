# Veltrix Collective — AI Session Instructions

## On every session start
1. Read the full project state: https://raw.githubusercontent.com/LukeJMadden/veltrix-collective/main/PROJECT_STATE.md
2. Do not ask the user to confirm information already in PROJECT_STATE.md
3. Use the exact variable names, secret names, and model strings documented there — do not invent or assume alternatives

---

## GitHub access
Repo: https://github.com/LukeJMadden/veltrix-collective  
Token: stored as GITHUB_PAT in user's environment — use the GitHub REST API to push files directly  
Push files via: PUT https://api.github.com/repos/LukeJMadden/veltrix-collective/contents/{path}

**Update PROJECT_STATE.md via GitHub API at the end of every session** where a milestone was completed, a script was built, a schema was changed, or a service was added. Never ask the user to update it manually.

---

## Core operating rules

### Always automate first
- If an action can be done via API or MCP (GitHub API, Supabase MCP, Notion MCP, browser JS), do it directly
- Only ask the user to perform a manual action if it genuinely cannot be automated
- If a currently manual action could be automated in future, tell the user exactly how after completing it

### What you can do directly (no user action needed)
- Push/update any file in the GitHub repo via GitHub REST API
- Run SQL against Supabase via Supabase MCP (project ID: qftpohuyvshbvhwxmkvn)
- Read/query Supabase tables to verify state before building
- Navigate and interact with web pages via Claude in Chrome
- Create/update Notion pages and databases via Notion MCP

### What requires the user
- Entering passwords or 2FA codes
- Approving purchases or financial transactions
- Actions inside services with no API (some UI-only dashboards)
- When explicit confirmation is needed before an irreversible action

### Before building any script or file
1. Check PROJECT_STATE.md for exact variable names, secret names, table schemas
2. Use the standard .yml env block and Python env reads from PROJECT_STATE.md
3. Use the standard call_ai() pattern (OpenAI primary, Claude fallback)
4. Never hardcode values that are already documented in PROJECT_STATE.md

---

## After completing any milestone

Update PROJECT_STATE.md via GitHub API with:
- Agent/script status changed to LIVE
- Any new env vars or secrets added
- Any schema changes
- Any new services added
- Build plan phase status updated

Commit message format: `[milestone] Brief description of what changed`

---

## Stack reference (quick lookup)
- Supabase project ID: qftpohuyvshbvhwxmkvn
- Hetzner VPS IP: 5.161.89.154 (Discord bot only — persistent WebSocket)
- GitHub Actions: all scheduled/cron agents
- Primary AI: OpenAI (gpt-4o / gpt-4o-mini)
- Fallback AI: Anthropic (claude-sonnet-4-6 / claude-haiku-4-5-20251001)
- Full schema, all env vars, all secret names: PROJECT_STATE.md