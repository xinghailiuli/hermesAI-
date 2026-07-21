---
name: coding-tools-server
description: Install and configure coding AI tools (Codex CLI, Claude Code, etc.) on the server and connect them to custom API backends (DeepSeek, SiliconFlow, etc.).
triggers:
  - install codex
  - setup codex
  - codex connect deepseek
  - codex cli
  - cc-switch
  - coding tool on server
  - Claude Code setup
  - AI coding tool proxy
---

# Coding AI Tools on Server

Install and wire up coding AI tools (Codex CLI, Claude Code) to work with
third-party API backends through the local relay or cc-switch.

## Codex CLI

### Installation

```bash
sudo npm install -g @openai/codex
# Verify: codex --version   (should show v0.140.0+)
```

### Protocol Incompatibility (Critical)

**Codex v0.140.0 uses the OpenAI Responses API over WebSocket by default.**
It does NOT fall back to HTTP Chat Completions — even with
`responses_websockets = false` in config.toml and
`-c features.responses_websockets=false` at runtime, Codex still opens a
WebSocket connection. Standard API relays only implement Chat Completions,
so a **protocol bridge** is mandatory.

The bridge must:
1. Accept WebSocket connections on `/v1/responses`
2. Send a `session.created` event on connection (Codex expects model info)
3. Read incoming WS messages — **the full prompt is in `instructions` (20K+ chars), NOT in `input` (which is empty on turn 1).** See `references/ws-message-format.md` for the message structure.
4. Pass `instructions` directly as the user message to the upstream LLM via Chat Completions
5. Convert the HTTP response back to Responses API WebSocket events (`response.created` → `response.in_progress` → `response.output_item.added` → `response.content_part.added` → `response.output_text.delta` → `response.content_part.done` → `response.output_item.done` → `response.completed`)
6. **Keep the WS connection OPEN** — closing after one response breaks Codex's agent loop; it reconnects and restarts the conversation from scratch
7. Accumulate conversation history across turns (append assistant responses for context continuity)

**Critical: `instructions` vs `input`**
- Turn 1: `instructions` = full system prompt + user message (20,771 chars), `input` = `[]` (empty)
- Turn 2+: `instructions` = same full prompt, `input` = developer messages (permissions, env context)
- The bridge MUST pass `instructions` as the primary content. Extracting from `input` alone produces empty messages → model only sees system prompt → endless role-acknowledgment loop

### Solution: Custom WebSocket Bridge (Working)

The api-relay skill provides a working bridge template:
`api-relay → templates/codex_ws_bridge.py`

Full message format reference: `references/ws-message-format.md` — documents the
exact WebSocket message structure, event sequence, and the critical `instructions`
vs `input` field distinction.

Architecture:
```
Codex CLI → ws://127.0.0.1:8848/v1/responses (WebSocket)
         → codex_ws_bridge.py (WS→HTTP translation)
         → Flask relay :8847/v1/chat/completions (HTTP)
         → DeepSeek API → response flows back
```

Port layout: **bridge on 8848, Flask relay on 8847** (bridge takes the port Codex expects).

The bridge reads the relay's auth token from `config.json` so `CODEX_API_KEY`
must match `config.json` → `auth.local_token` exactly. Mismatched tokens
cause 401 Unauthorized on HTTP probe routes (visible in `codex doctor`).

The bridge logs to `/tmp/codex_bridge.log` — always check this when debugging.

### Alternative: cc-switch

cc-switch is an external tool that does the same protocol translation. It works
but requires downloading from GitHub (may be blocked by GFW/GnuTLS SSL issues).
The custom bridge is self-contained and preferred for server deployments.

| Tool | Type | Best For |
|------|------|----------|
| Custom bridge (api-relay template) | Python/aiohttp | Server, self-contained |
| [farion1231/cc-switch](https://github.com/farion1231/cc-switch) | Desktop GUI (Tauri) | Local PC |
| [SaladDay/cc-switch-cli](https://github.com/SaladDay/cc-switch-cli) | CLI | Servers (if downloadable) |

### Configuration (config.toml) — Minimal Working

Codex reads `~/.codex/config.toml`. The `[model_providers]` section is **not needed**
for custom endpoints — just set `openai_base_url`:

```toml
# Minimal working config for bridge setup
openai_base_url = "http://127.0.0.1:8848/v1"

[network]
proxy_url = "http://127.0.0.1:7897"

[features]
responses_websockets = false
responses_websockets_v2 = false
```

Note: `responses_websockets = false` is **ignored** by Codex v0.140.0 — it still
uses WebSocket. Keep it for forward compatibility but don't rely on it.

### Environment Variables

```bash
# MUST match config.json → auth.local_token, not a random DeepSeek key
export CODEX_API_KEY="sk-local-apirelay-2026"
```

Codex uses `CODEX_API_KEY` as the Bearer token for all API calls.
The bridge proxies the Authorization header as-is to Flask, so the token
must match what Flask expects. Use `python3 -c` to read the exact token
from config.json if the tool output appears truncated (see api-relay skill
pitfalls about tool truncation).

### Diagnostics

```bash
codex doctor           # Full health check — shows base URL, WS endpoint, auth mode, route probes
codex exec --help      # Available flags
```

`codex doctor` is the single most valuable debug tool. It shows:
- `openai API base URL` — confirms config.toml is being read
- `websocket endpoint` — confirms which WS endpoint Codex will use
- `handshake result` — HTTP 101 = bridge accepted, other = problem
- `openai API route probe` — HTTP 401 = auth mismatch, 404 = missing endpoint

### Key Flags

- `-c model=deepseek-chat` — override model (required; default is gpt-5.5)
- `--skip-git-repo-check` — required when not in a trusted git repo
- `-c features.responses_websockets=false` — attempt WS disable (doesn't work)
- `-m MODEL` — shorthand for model override
- `--oss` / `--local-provider` — for local models ONLY, not custom endpoints

### Pitfalls

- **`responses_websockets = false` is IGNORED.** Codex v0.140.0 always opens WebSocket. The bridge must handle WS — no amount of config flagging prevents it.
- **Bridge must stay open.** Closing the WS after one response causes Codex to reconnect and restart the conversation loop from scratch → infinite timeout. The bridge must accumulate conversation history and handle multiple turns on the same connection.
- **`CODEX_API_KEY` must match relay's `local_token` exactly.** Not a DeepSeek/SiliconFlow API key — it's the local relay's auth token. Length mismatches are a common 401 cause (check with `python3 -c` to see full token, not tool-truncated output).
- **`-c model=deepseek-chat` is mandatory.** Without it, Codex defaults to `gpt-5.5` which the relay won't recognize → 404 or fallback errors.
- **`--skip-git-repo-check` required outside git repos.** Codex refuses to run in non-trusted directories without this flag.
- **Never use `--oss` for custom API endpoints.** `--oss` mode only works with LM Studio or Ollama local servers.
- **`codex exec` reads prompt from stdin by default** — pass as positional argument, or pipe.
- **Model metadata warning** (`Model metadata for 'deepseek-chat' not found`) is cosmetic — Codex falls back to defaults and works fine.
- **`session.created` event is optional but helpful** — sending it on WS connection reduces `server model present: false` warning in `codex doctor`. Not required for functionality.
- **`codex exec --max-turns N` is not a valid flag.**
- **`[model_providers]` config section is unnecessary** for the bridge approach. The `openai_base_url` key alone is sufficient.

## Reference files

- `references/ws-message-format.md` — Full WebSocket message structure for Responses API bridge
- `references/github-gfw-download.md` — Downloading GitHub release assets from behind GFW (ghproxy.net, aria2c, direct CDN methods)
