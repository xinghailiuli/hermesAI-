---
name: hermes-dashboard
description: Set up and run Hermes Agent web dashboard with browser-based chat UI. Use when user wants a web interface instead of CLI/PowerShell.
category: troubleshooting
---

# Hermes Dashboard Web UI

Set up the Hermes Agent browser-based dashboard with chat functionality (`--tui`), so the user can interact with the agent from a web browser instead of a terminal.

## Quick Start

```bash
# 1. Install web dependencies (one-time)
~/.local/share/pipx/venvs/hermes-agent/bin/python -m pip install fastapi uvicorn websockets

# 2. Start dashboard with chat TUI
hermes dashboard --tui --port 9119

# 3. Open in Windows browser (from WSL)
# http://localhost:9119
```

## Pitfalls

- **Do NOT use `--host 0.0.0.0`** — Hermes rejects it for security reasons (exposes API keys). Use default 127.0.0.1 and rely on WSL2 localhost forwarding.
- **Dependencies must be installed in the pipx venv**, not globally. Use the full path to the venv's python: `~/.local/share/pipx/venvs/hermes-agent/bin/python -m pip install ...`
- **`pip` command may not exist** in the venv's bin/ — use `python -m pip` instead.
- **Default port is 9119**. Avoid ports below 1024 (require root).
- **Gateway/dashboard token desync**: If the gateway was already running when the dashboard starts, the session token injected into the dashboard HTML (`window.__HERMES_SESSION_TOKEN__`) may not match the gateway's WebSocket auth state. The browser frontend will show "Failed to fetch" or "WebSocket auth failed" (the JS bundle contains multi-language auth-failure messages). Two fixes:
  1. **Hard refresh** (`Ctrl+Shift+R`) — the dashboard backend issues a fresh token on page load; often the simplest fix.
  2. **Restart the gateway** (`hermes gateway restart`) — guarantees token sync but briefly interrupts any active CLI session.
- **Browser proxy hijacks localhost**: When using Clash Verge with TUN mode or system proxy, the browser may route even `localhost` traffic through the proxy, which then fails to reach the WSL2 service. Symptom: `curl` and `powershell.exe` both return 200, but the browser says "refused to connect." Fixes (try in order):
  1. Add `localhost` / `127.0.0.1` to the proxy bypass list (Clash Verge → Settings → Bypass)
  2. Use a different browser that isn't proxied (e.g. Edge if Chrome has the proxy)
  3. Temporarily disable system proxy in Clash Verge

## Windows Firewall

If the browser on Windows can't reach localhost:9119, add a firewall rule:

```powershell
# Run in Windows PowerShell (Admin)
New-NetFirewallRule -DisplayName "Hermes Dashboard" -Direction Inbound -Protocol TCP -LocalPort 9119 -Action Allow
```

## Troubleshooting Flow

When the user says "dashboard doesn't work," diagnose in this order:

```
1. Dashboard running?
   → ss -tlnp | grep 9119
   NO  → start: hermes dashboard --tui --port 9119

2. Dashboard backend responding?
   → curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9119
   NO  → check deps, check for port conflict

3. WSL2→Windows forwarding works?
   → powershell.exe -Command "Invoke-WebRequest ..."
   NO  → WSL2 localhost forwarding broken; try WSL IP directly

4. Browser shows "Failed to fetch" or "WebSocket auth failed"?
   → token desync → hard refresh or restart gateway

5. Browser shows "refused to connect" but PowerShell returns 200?
   → browser proxy hijacking localhost → bypass list or different browser
```

## Verification

```bash
# From WSL
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:9119
# Expected: 200

# From Windows (via WSL)
powershell.exe -Command "Invoke-WebRequest -Uri http://localhost:9119 -TimeoutSec 5 | Select-Object StatusCode"
# Expected: 200
```

## Tabs

- **Config**: Manage model, API keys, tools
- **Sessions**: Browse and resume past conversations
- **Chat** (`--tui`): Embedded terminal chat with the agent
