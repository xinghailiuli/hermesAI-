# DeepSeek-Compatible Coding Terminal Tools

Terminal coding assistants that work natively with DeepSeek API (via OpenAI-compatible endpoints).

## 1. CodeWhale (Hmbown/CodeWhale) — DeepSeek版Claude Code

- **Author**: Hunter Bown (Hmbown)
- **Stars**: 34,500+
- **Language**: Rust
- **Repo**: https://github.com/Hmbown/CodeWhale
- **Description**: "Agentic coding terminal. DeepSeek-first, multi-provider, cache-maximal, whale-themed"

### Binary Names (Critical)
- `codewhale` — main CLI (18MB)
- `codewhale-tui` — full terminal UI (50MB)
- `deepseek-tui` — ⚠️ DEPRECATED wrapper, just calls `codewhale-tui`. Do NOT use as install target.

### Installation
```bash
curl -L -o /usr/local/bin/codewhale \
  https://github.com/Hmbown/CodeWhale/releases/download/v0.8.44/codewhale-linux-x64
chmod +x /usr/local/bin/codewhale
```

### Configuration
```bash
export DEEPSEEK_BASE_URL=http://127.0.0.1:8848/v1
export DEEPSEEK_API_KEY=sk-local-apirelay-2026
```

## 2. DeepSeekCode (willamhou/DeepSeekCode)

- **Author**: William Hou
- **Stars**: ~1
- **Language**: Rust
- **Repo**: https://github.com/willamhou/DeepSeekCode
- **Size**: 4.3MB tar.gz
- **Description**: "DeepSeek-powered Rust coding agent, CLI, and terminal TUI"

### Binary Names
- `deepseek` — binary inside tar.gz
- Install as `/usr/local/bin/dscode` to avoid name collision

## 3. Aider

- **Language**: Python, `pip install aider-chat`
- Config at `~/.aider.conf.yml`
- Large package, often times out behind slow proxies

## Download Workarounds

Proxy nodes often throttle `release-assets.githubusercontent.com`.

| Method | Works? |
|--------|--------|
| Direct curl via proxy | ❌ SSL_ERROR_SYSCALL |
| git clone --depth 1 | ✅ Different CDN |
| User downloads + SCP | ✅ Best |
| QQ file attachment | ❌ QQ repackages, unextractable |
