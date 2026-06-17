# Third-Party Coding Assistants via API Relay

The relay's OpenAI-compatible and Anthropic-compatible endpoints allow popular
coding assistants to run through local providers (DeepSeek, 百炼, etc.).

---

## Claude Code (Anthropic CLI)

**What it is**: Anthropic's official terminal coding agent. Uses Anthropic Messages
API natively — needs the `/v1/messages` translation layer.

### Install

```bash
# Requires Node.js ≥18. On Chinese cloud servers, configure npm proxy first:
npm config set registry https://registry.npmjs.org/   # NOT npmmirror (missing native deps)
npm config set proxy http://127.0.0.1:7897
npm config set https-proxy http://127.0.0.1:7897

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs

# Install Claude Code (global)
sudo npm install -g @anthropic-ai/claude-code

# ⚠️ If native binary missing, install it separately + symlink:
sudo npm install -g @anthropic-ai/claude-code-linux-x64
sudo ln -sf /usr/lib/node_modules/@anthropic-ai/claude-code-linux-x64/claude /usr/local/bin/claude
```

**Pitfalls**:
- **淘宝镜像缺原生包**: `registry.npmmirror.com` 没有 `@anthropic-ai/claude-code-linux-x64` 原生
  依赖，会导致 `claude native binary not installed` 错误。必须切回 npm 官方源 + 代理。
- **残留目录**: `npm install` 中断后残留 `/usr/lib/node_modules/@anthropic-ai/claude-code`，
  下次安装报 `ENOTEMPTY`。先 `sudo rm -rf` 清掉。

### Configure

Claude Code reads `ANTHROPIC_BASE_URL` and `ANTHROPIC_API_KEY` env vars:

```bash
export ANTHROPIC_BASE_URL="http://localhost:8848"
export ANTHROPIC_API_KEY="sk-local-apirelay-2026"
```

For permanent setup, add to `~/.bashrc`.

### Usage

```bash
# One-shot (--print: non-interactive, works without --bare)
claude --print "explain this code"

# Interactive REPL (--bare needed to skip OAuth/keychain prompts)
claude --bare
```

`--print` / `-p` works without `--bare` because it's non-interactive.
For interactive sessions, `--bare` is required to skip OAuth/keychain
and read `ANTHROPIC_API_KEY` from the environment.

**Model mapping** is handled by `anthropic_model_map` in `config.json`:
- `claude-sonnet-4-6` → `deepseek-chat`
- `claude-opus-4-5` → `deepseek-reasoner`

**Tool calling is limited** — Claude Code's tool-use prompts pass through the
translation layer, but the Anthropic ↔ OpenAI tool format conversion is
simplified. Simple chat and code generation work reliably; complex agentic
workflows may need further tuning of `anthropic_to_openai()` tool translation.

---

## CodeWhale / DeepSeek-TUI (Rust, 34k⭐)

**What it is**: `Hmbown/CodeWhale` — the renamed `deepseek-tui`, a full-featured
Rust terminal coding agent that implements the Claude Code interaction model with
DeepSeek API natively. 34k+ GitHub stars. Apache 2.0 licensed.

Repo: https://github.com/Hmbown/CodeWhale

### Architecture (dual binary)

CodeWhale requires TWO binaries in the same directory:

| File | Size | Purpose |
|------|------|---------|
| `codewhale` | ~18MB | CLI dispatcher (npm publishes this as JS wrapper) |
| `codewhale-tui` | ~50MB | Core TUI runtime engine |

The `codewhale` dispatcher looks for `codewhale-tui` in the same directory.
Set `DEEPSEEK_TUI_BIN` env var to override the tui binary path.

### Install

```bash
# Option A: npm (preferred — auto-downloads both binaries)
sudo npm install -g codewhale

# Option B: manual (when GitHub is blocked)
# Download from https://github.com/Hmbown/CodeWhale/releases/latest
# Place BOTH codewhale AND codewhale-tui in /usr/local/bin/
```

⚠️ **npm install on cloud servers**: The npm package downloads real binaries
from GitHub Releases during `postinstall`. If GitHub is blocked (common on
Chinese cloud servers with restrictive proxies), the JS wrappers will be
installed but binaries won't download. See download troubleshooting below.

## DeepSeekCode (Rust, lightweight)

**What it is**: `willamhou/DeepSeekCode` — a lightweight Rust terminal coding
agent for DeepSeek. Uses OpenAI-compatible API natively. MIT licensed.

Repo: https://github.com/willamhou/DeepSeekCode

### Install

Single self-contained binary (~11 MB). No Node.js/Python runtime needed.

```bash
# Extract from release tarball
tar xzf deepseek-linux-x64.tar.gz
sudo cp deepseek /usr/local/bin/
sudo chmod +x /usr/local/bin/deepseek
```

### Configure

```bash
export DEEPSEEK_API_KEY="sk-local-apirelay-2026"
```

Config file `~/.dscode/config.toml`:
```toml
model.base_url = "http://localhost:8848/v1"
model.model = "deepseek-chat"
model.api_key_env = "DEEPSEEK_API_KEY"
```

### Usage

```bash
deepseek run "fix the failing tests"    # One-shot task
deepseek chat                            # Interactive REPL
deepseek tui                             # Full-screen terminal workbench
deepseek --version                       # v0.1.5
```

---

## Comparison

| | Claude Code | Codex | CodeWhale | DeepSeekCode |
|---|---|---|---|---|
| Language | Node.js (npm) | Node.js (npm) | Rust (binary ×2) | Rust (binary) |
| API format | Anthropic | OpenAI Responses (WS) | OpenAI native | OpenAI native |
| Transport | HTTP SSE | **WebSocket** | HTTP | HTTP |
| Size | ~200MB (npm deps) | ~300MB (npm deps) | ~68MB (2 binaries) | ~11MB |
| Works via relay? | ✅ via `/v1/messages` | ✅ via WS bridge (with tool exec) | ✅ native | ✅ native |
| GitHub stars | — | — | 34k+ | ~500 |

---

## Codex (OpenAI CLI)

**What it is**: OpenAI's official coding agent CLI. Uses the **Responses API** over
**WebSocket** — fundamentally different from the standard Chat Completions HTTP API.
Requires a protocol bridge to work through the API relay.

### Install

```bash
sudo npm install -g @openai/codex
```

### Architecture challenge

Codex does NOT use standard `/v1/chat/completions`. It connects via WebSocket to
`/v1/responses` and exchanges JSON messages in the Responses API format:

```
WS → {"model":"...", "input":"...", "instructions":"...", "tools":[...]}
WS ← {"type":"response.created", "response":{...}}
WS ← {"type":"response.output_item.added", ...}
WS ← {"type":"response.content_part.added", ...}
WS ← {"type":"response.output_text.delta", "delta":"..."}
WS ← {"type":"response.content_part.done", ...}
WS ← {"type":"response.output_item.done", ...}
WS ← {"type":"response.completed", "response":{...}}
```

The API relay's Flask server can't handle WebSocket natively, so a
**WebSocket-to-HTTP bridge** is required. The bridge:
1. Listens on port 8848, accepts WS connections at `/v1/responses`
2. Proxies all HTTP requests to Flask relay on 8847
3. Translates Responses API ↔ Chat Completions format

### Bridge prototype

A working aiohttp-based bridge exists at `~/api-relay/codex_ws_bridge.py`:

```bash
# Flask relay on 8847 (set in config.json: server.port = 8847)
# Bridge on 8848 (proxies HTTP → 8847, handles WS natively)
python3 ~/api-relay/codex_ws_bridge.py
```

**✅ Status as of 2026-06-17: FULLY WORKING.** Codex CLI v0.140.0 → WS bridge →
Flask relay → DeepSeek API — end-to-end pipeline verified with exit code 0.

The bridge logs all activity to `/tmp/codex_bridge.log` — always check this
file when debugging connectivity or auth issues.

### Codex config (`~/.codex/config.toml`)

```toml
openai_base_url = "http://127.0.0.1:8848/v1"

[network]
proxy_url = "http://127.0.0.1:7897"

[features]
responses_websockets = false       # NOTE: Codex v0.140.0 ignores this
responses_websockets_v2 = false    # NOTE: Codex v0.140.0 ignores this
```

### Verified working command

```bash
export CODEX_API_KEY="sk-local-apirelay-2026"

# With sandbox (bwrap must be installed and user namespaces enabled)
codex exec "your prompt" -c model=deepseek-chat --skip-git-repo-check -s workspace-write

# Without sandbox (for servers where bwrap loopback fails)
codex exec "your prompt" -c model=deepseek-chat --skip-git-repo-check \
  --dangerously-bypass-approvals-and-sandbox
```

**Sandbox modes**: `read-only` (default) | `workspace-write` | `danger-full-access`
When `bwrap: loopback` error occurs, either fix user namespace config or use
`--dangerously-bypass-approvals-and-sandbox` for trusted environments.

### bwrap sandbox fix (Ubuntu 24.04)

When `bwrap: loopback` or `bwrap: setting up uid map: Permission denied` prevents
Codex from executing tool calls, fix in this order:

```bash
# 1. Install required packages
sudo apt install -y uidmap bubblewrap

# 2. Check if AppArmor is blocking user namespaces
cat /proc/sys/kernel/apparmor_restrict_unprivileged_userns
# If output is "1", disable it:
sudo sysctl -w kernel.apparmor_restrict_unprivileged_userns=0

# 3. Ensure subuid/subgid mappings include the user's real UID
grep "^$USER:" /etc/subuid
# Should show at least: admin:1000:1  OR  admin:100000:65536
# If the user's real UID (1000 in this example) isn't mapped, add it:
echo "$USER:$(id -u):1" | sudo tee -a /etc/subuid
echo "$USER:$(id -u):1" | sudo tee -a /etc/subgid

# 4. Verify bwrap works
bwrap --ro-bind / / -- true && echo "bwrap OK!"
```

### Critical requirements

1. **Bridge must stay open (persistent WS).** Closing the WS after one response
   breaks Codex's agent loop — it reconnects and restarts from scratch → timeout.
   The bridge accumulates conversation history across turns on the same connection.

2. **`CODEX_API_KEY` must match `config.json` → `auth.local_token` exactly.**
   Not a DeepSeek API key — it's the local relay's auth token. Length mismatches
   are a common 401 cause (verify with `python3 -c` to see full token).

3. **`-c model=deepseek-chat` is mandatory.** Without it, Codex defaults to
   `gpt-5.5` which the relay won't recognize.

4. **`codex doctor` is the best diagnostic tool.** It shows the actual endpoint
   Codex will use, the WS handshake result, and HTTP route probe status.

### Key pitfalls

- **`responses_websockets = false` is silently ignored** by Codex v0.140.0.
  Codex ALWAYS opens a WebSocket — no config flag prevents it. The bridge
  must handle WS regardless.
- **Don't close WS after one response** — causes infinite reconnect/timeout loop.
- **`codex exec` reads prompt from stdin OR positional arg** — both work:
  `codex exec "hi"` or `echo "hi" | codex exec`
- **`--skip-git-repo-check` required** outside git repos
- **Model metadata warning** (`not found. Defaulting to fallback`) is cosmetic
  but can be silenced by enriching `/v1/models` with `context_window`,
  `max_output_tokens`, etc. (see server.py `list_models()`)
- **Bridge token is read from `config.json` at startup** — not hardcoded.
  Update `config.json` and restart the bridge to change the auth token.

### Relay-side improvements for Codex

**Model metadata endpoint** — Codex probes `/v1/models` and
`/v1/models/{model_id}` at startup (`codex doctor` shows whether
`server model present` and `models etag present`). The relay should
return rich model metadata to avoid the fallback warning:

```python
models.append({
    'id': m['id'], 'object': 'model',
    'created': 1765900800, 'owned_by': m['provider'],
    'context_window': 128000, 'max_output_tokens': 16384,
    'supports_structured_output': True,
    'supports_streaming': True,
    'supports_tool_calling': True,
})
```

**Chinese language auto-detection** — the bridge detects CJK characters
in the user's first message and appends a language instruction to the
system prompt: `"Respond in Chinese (Simplified)."` This biases DeepSeek
responses toward Chinese when the user writes in Chinese, without affecting
English prompts. Detection runs against the full `instructions` + `input`
content, not just the extracted user message.

**Root endpoint (`/v1`, `/v1/`)** — Codex's `doctor` probes `HEAD /v1` as
part of its reachability check. Without a root route, it reports
`reachable (HTTP 404)`. Flask must serve a minimal response at `/` and `/v1`:

```python
@app.route('/')
@app.route('/v1')
@app.route('/v1/')
def api_root():
    return jsonify({'object': 'list', 'data': [], 'message': 'API relay running'})
```

**WebSocket session.created event** — When Codex opens a WS connection,
it expects the server to advertise model capabilities via a `session.created`
event BEFORE processing any turns. Without it, `codex doctor` reports
`server model present: false`. The bridge sends this immediately after
`ws.prepare()`:

```python
await ws.send_json({
    "type": "session.created",
    "session": {
        "id": f"sess_{uuid.uuid4().hex[:24]}",
        "model": "deepseek-chat",
        "modalities": ["text"],
        "context_window": 128000,
        "max_output_tokens": 16384,
        "temperature": 0.7,
    }
})
```

**Markdown bash → ToolCall conversion (✅ WORKING)** — DeepSeek outputs\nmarkdown code blocks, but Codex needs structured `function_call` events\nto execute commands. The bridge implements a conversion pipeline:\n\n1. **Regex extraction**: `` ```bash\\s*\\n([\\s\\S]*?)\\n``` `` captures pure\n   shell scripts, stripping markdown wrapping and model chatter.\n\n2. **Tool call format** (verified working with Codex v0.140.0):\n   ```python\n   {\n       \"call_id\": f\"call_{uuid}\",\n       \"name\": \"exec_command\",        # NOT \"bash\" or \"Bash\"\n       \"arguments\": {\n           \"cmd\": \"echo hello\",       # NOT \"command\" or \"script\"\n           \"description\": \"say hello\"  # first line of script, ≤100 chars\n       }\n   }\n   ```\n\n3. **Required WS events** (in order):\n   ```python\n   {\"type\": \"response.output_item.added\", \"item\": {{\"type\": \"function_call\",\n    \"call_id\": ..., \"name\": \"exec_command\", \"status\": \"in_progress\"}}}\n   {\"type\": \"response.function_call_arguments.delta\", \"delta\": args_json}\n   {\"type\": \"response.output_item.done\", \"item\": {{\"type\": \"function_call\",\n    \"call_id\": ..., \"name\": \"exec_command\", \"status\": \"completed\",\n    \"arguments\": args_json}}}\n   ```\n   The `response.function_call_arguments.delta` event is REQUIRED — without it\n   Codex won't execute the tool call.\n\n4. **Error messages as compass**:\n   - `unsupported call: bash` → wrong tool name (use `exec_command`)\n   - `missing field 'cmd'` → wrong argument name (use `cmd`, not `command`)\n   - `websocket closed before response.completed` → event sequence broken\n   - No error, file not created → likely `bwrap: loopback` sandbox issue\n\n5. **Function call output handling** — After Codex executes a tool call, it\n   sends back a `function_call_output` in subsequent WS messages. The bridge\n   passes these through in the messages array so DeepSeek sees execution\n   results and can respond appropriately.\n\n6. **System prompt optimization** — Add to bridge system hints:\n   \"When executing terminal commands, output ONLY a ```bash code block with\n   the exact commands. No explanations.\" This reduces verbose output and\n   increases the chance of clean bash block extraction.\n\n7. **Text cleanup after extraction** — Strip bash blocks from the assistant\n   text. If only bash remains, generate a minimal summary: \"执行命令: ...\"\n   or \"Running: ...\" based on language detection.

**`instructions` field is the primary payload** — Codex packs the entire
conversation context into the `instructions` field (20,771 characters on
first turn). The `input` field is `[]` on turn 1; on later turns it contains
developer messages with sandbox permissions and environment info. The bridge
must use `instructions` as the main user message source, appending `input`
content after a delimiter only when non-empty.

**Message construction (bridge)** — After extracting from `instructions`
and `input`, the bridge builds an OpenAI-formatted messages array. Language
detection runs on the full content. A compact system instruction is added
only when Chinese is detected (to avoid bloating English prompts).
Previous assistant responses are prepended to maintain conversation continuity
across turns on the same WS connection.

**`conversation` variable gotcha** — During the V5 rewrite, `conversation`
changed from being the messages array sent to the API to being a short-term
context buffer. The `messages` list (built fresh each turn from the current
`instructions` + `input`) is what gets sent to `/v1/chat/completions`.
The `conversation` list tracks only the last 2-4 assistant responses for
continuity context. Confusing the two causes empty or stale conversations
being sent to the API.

### Working alternatives (no WS bridge needed)

For immediate use, these tools work through the relay without protocol translation:

| Tool | Install | Config |
|------|---------|--------|
| **DeepSeekCode** | single binary ~11MB | `DEEPSEEK_API_KEY` + `~/.dscode/config.toml` |
| **CodeWhale** | npm or binary | Native OpenAI-compatible |
| **Claude Code** | npm | Works via `/v1/messages` endpoint |

---

## GitHub Download from China Cloud Servers

**Key insight**: mihomo proxy with `gw.alicdn.com` SNI disguise blocks ALL
GitHub-related domains (github.com, release-assets.githubusercontent.com,
Azure blob storage). But Alibaba Cloud has a direct route to `github.com`.

### Strategy (in priority order)

1. **Direct (no proxy)** — `curl --noproxy '*' https://github.com/...`
   - Works for `github.com` HTML pages and API
   - Fails for `release-assets.githubusercontent.com` (blocked in China)
   
2. **GitHub API through proxy** — `api.github.com` works through mihomo
   - Use to inspect releases, get asset IDs
   - Asset downloads redirect to Azure blob → BLOCKED

3. **npm install** — npm registry (`registry.npmjs.org`) usually works
   - But `codewhale` npm postinstall fetches binaries from GitHub → BLOCKED
   - Result: JS wrappers install, binaries fail

4. **QQ file transfer (last resort)** — split large files and send via QQ
   ```bash
   # On local machine (WSL):
   split -b 9M codewhale-tui-linux-x64 ctui_part_
   # Send each part via QQ → cloud merges:
   cat ctui_part_* > codewhale-tui-linux-x64
   ```

5. **Mirror sites** — tested and NONE worked for release assets:
   ghproxy.net, ghproxy.com, gh.ddlc.top, gh.con.sh, gh.api.99988866.xyz,
   gh.llkk.cc, gh2.yanqishui.work, github.moeyy.xyz, download.fastgit.org,
   hub.fastgit.xyz, github.com.cnpmjs.org — all timeout or 403
