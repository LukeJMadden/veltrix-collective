# Composio MCP — 401 Fix for Claude Desktop (Windows)

## Symptom
Claude Desktop shows `mcp-config-hxmhed — failed / Server disconnected`  
Logs show: `Server returned 401 after successful authentication`

## Root Cause
The `mcp-remote` OAuth flow is broken on Composio's platform. The setup command installs correctly but the OAuth token is rejected by Composio's server after completion.

## Fix — Bypass OAuth with API Key Header

### Step 1 — Get your Composio API key
Go to: `platform.composio.dev` → Settings → API Keys → copy your key

### Step 2 — Edit Claude Desktop config
Open PowerShell and run:
```powershell
notepad "$env:APPDATA\Claude\claude_desktop_config.json"
```

Replace the `mcp-config-hxmhed` block with this (keep your existing `preferences` block intact):

```json
{
  "mcpServers": {
    "mcp-config-hxmhed": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "https://backend.composio.dev/v3/mcp/c87e99ef-e4a5-4294-808b-58afb31531d7/mcp?user_id=pg-test-cab455b4-3482-4a0e-a206-e14fda773ff5",
        "--header",
        "x-api-key:YOUR_COMPOSIO_API_KEY_HERE"
      ],
      "env": {
        "npm_config_yes": "true"
      }
    }
  },
  "preferences": {
    "coworkScheduledTasksEnabled": true,
    "ccdScheduledTasksEnabled": true,
    "sidebarMode": "chat",
    "coworkWebSearchEnabled": true
  }
}
```

Replace `YOUR_COMPOSIO_API_KEY_HERE` with your actual key. Do not add quotes around the key — the format is `x-api-key:theactualkey` with no spaces.

### Step 3 — Fully restart Claude
Right-click the Claude icon in the system tray → **Quit**  
Then reopen Claude. The MCP server should connect with no OAuth browser window.

---

## If you need to re-run initial setup first
```powershell
# Clear old cache
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\npm-cache" -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force "$env:USERPROFILE\.mcp-remote" -ErrorAction SilentlyContinue

# Re-run setup
npx @composio/mcp@latest setup "YOUR_MCP_URL" "mcp-config-hxmhed" --client claude
```

Then apply the fix in Step 2 above before restarting Claude.

---

## Notes
- The MCP URL is permanent — it does not change when you reconnect or recreate the server
- Your MCP URL: `https://backend.composio.dev/v3/mcp/c87e99ef-e4a5-4294-808b-58afb31531d7/mcp?user_id=pg-test-cab455b4-3482-4a0e-a206-e14fda773ff5`
- Issue confirmed present as of March 2026
