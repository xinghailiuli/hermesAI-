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

| | Claude Code | CodeWhale | DeepSeekCode |
|---|---|---|---|
| Language | Node.js (npm) | Rust (binary ×2) | Rust (binary) |
| API format | Anthropic | OpenAI native | OpenAI native |
| Size | ~200MB (npm deps) | ~68MB (2 binaries) | ~11MB |
| MCP support | Via `--mcp-config` | Built-in | Built-in |
| TUI | No | Yes | Yes |
| GitHub stars | — | 34k+ | ~500 |

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
