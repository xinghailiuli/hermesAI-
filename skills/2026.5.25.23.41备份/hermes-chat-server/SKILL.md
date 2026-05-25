---
name: hermes-chat-server
description: Build web chat interfaces for Hermes Agent. FastAPI bridge + single-file HTML frontend with theme switching, session continuation, and Windows auto-start.
category: web-dev
---

# Hermes Chat Server

Trigger: user wants a browser-based chat UI for Hermes Agent (not CLI), wants auto-start, wants custom themes/styling.

## Architecture

A two-layer system:
1. **Python FastAPI backend** — bridges `hermes chat -q` to HTTP API
2. **Single-file HTML frontend** — styled chat interface in browser

```
Browser (HTML/CSS/JS)  →  fetch POST /api/chat  →  FastAPI server  →  hermes chat -q "message"
                         ←  JSON {response, session_id}  ←                ←  (stdout)
```

## Backend: FastAPI Server

Key endpoints:
- `POST /api/chat` — sends message to hermes, returns response + session_id
- `POST /api/new-session` — clears session, starts fresh
- `GET /api/status` — health check
- `GET /` — serves the HTML frontend

### Running hermes programmatically

```python
cmd = ["hermes", "chat", "-q", query]
if session_id:
    cmd.extend(["--resume", session_id])

result = subprocess.run(cmd, capture_output=True, text=True, timeout=300,
    env={**os.environ, "NO_COLOR": "1"})
```

Use `--resume <session_id>` for conversation continuity. The session ID is found by regex `--resume (\S+)` in the output.

### Response parsing

`hermes chat -q` output has terminal decorations. Strip them:

```python
import re
# Remove ANSI codes
clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', output)

# Split on separator blocks (───)
parts = re.split(r'─{3,}', clean)
# parts[2] is the actual response content (between header and footer separators)
content = parts[2].strip() if len(parts) >= 4 else ""

# Fallback: filter out known noise lines
noise = ["Query:", "Initializing", "Browser engine", 
         "Resume this session", "Session:", "Duration:", "Messages:"]
```

### Session persistence

Save `session_id` to a JSON file so the server restarts don't lose context:

```python
SESSION_FILE = Path.home() / ".hermes" / "chat_sessions" / "current_session.json"
```

## Frontend: Single-File HTML

### Theme System (CSS Custom Properties)

Six presets via class-based switching on `<body>`:

```css
:root { /* dark theme - default */ }
.theme-pink { --bg: #1a1025; --accent: #ff6b9d; ... }
.theme-gold { --bg: #1a1a10; --accent: #ffd700; ... }
.theme-green { --bg: #0a1a10; --accent: #50e890; ... }
.theme-ocean { --bg: #0a1525; --accent: #4ea8e8; ... }
.theme-light { --bg: #f5f5f7; --text: #1a1a2e; ... }
```

Persist preference in `localStorage('hermes-theme')`. Update on load:
```javascript
document.body.className = themeClasses[theme] || '';
```

### Chat UI patterns

- Message bubbles: `.message.user` and `.message.ai` with avatars
- Auto-scroll: `chatArea.scrollTop = chatArea.scrollHeight`
- Loading state: pulsing dots via CSS animation on the loading bubble
- Empty state: quick-prompt buttons that populate the input and send
- Enter to send, Shift+Enter for newline

### CSS variables to customize per theme

```
--bg (page), --bg2 (header/footer), --card (panels), 
--text, --text2 (muted), --accent, --accent2, 
--bubble-user, --bubble-ai, --input-bg, --border, --hover
```

## Auto-Start on Windows

Use `schtasks.exe` to create a login-triggered task:

```bash
schtasks.exe /Create /SC ONLOGON /TN "HermesChatServer" \
  /TR "wsl.exe -d Ubuntu --exec /path/to/python /path/to/server.py" \
  /F /RL HIGHEST /DELAY 0001:00
```

Desktop shortcut (`.url` file) for quick access:
```
[InternetShortcut]
URL=http://localhost:9118
```

## Pitfalls

- **PowerShell encoding from WSL**: Writing `.ps1` files with Chinese/emoji characters from WSL causes encoding errors. Use `schtasks.exe` directly instead of PowerShell scripts for task creation.
- **Port conflict**: Don't use port 9119 (Hermes Dashboard default). Use 9118 or another free port.
- **Session parsing regex**: The `--resume` hint may appear on either stdout or stderr. Search both.
- **ANSI in output**: Always set `NO_COLOR=1` env var and strip ANSI escape codes before displaying to web.
- **Timeout**: `hermes chat -q` can take 30-120s. Set subprocess timeout to 300s.

## Reference Files

- `references/wsl-proxy-setup.md` — Troubleshooting WSL2 proxy connectivity with Clash Verge / V2Ray
