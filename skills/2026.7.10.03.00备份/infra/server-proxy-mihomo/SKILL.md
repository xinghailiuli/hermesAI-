---
name: server-proxy-mihomo
description: Configure mihomo (Clash Meta) proxy on Linux cloud servers behind GFW. Covers install, vmess config, GeoIP pitfall, env vars, and verification.
triggers:
  - proxy
  - 翻墙
  - 科学上网
  - Clash
  - mihomo
  - vmess
  - 机场
  - 服务器上不了GitHub
  - 被墙
  - GFW
  - 配置代理
---

# Server Proxy Setup with Mihomo

Set up mihomo (Clash Meta kernel) on a headless Linux server to route traffic through vmess/vless/ss nodes.

## ⚠️ OPERATIONAL RULE: Always Use Proxy for External Requests

**If mihomo is running on this server, ALL external HTTP requests MUST go through the proxy.** Do not try `curl https://...` directly — always use `-x http://127.0.0.1:7897` (or the configured `mixed-port`). This applies to: `curl`, Python `urllib`, `requests`, `wget`, and any other HTTP client.

**Check before making any external request:**
```bash
# Is mihomo running?
pgrep mihomo && echo "Proxy is UP — use -x http://127.0.0.1:7897" || echo "Proxy is DOWN"
```

If mihomo is running but you didn't use the proxy, the user will notice the repeated failures and correct you. Save them the trouble.

## Prerequisites

- Linux server with root/sudo access
- A working vmess/vless subscription or node config
- The server cannot reach GitHub directly (catch-22: need proxy to download proxy)

## Step 1: Download mihomo Binary

Since GitHub is blocked, use a mirror or upload the binary:

```bash
# Option A: From local machine
scp mihomo-linux-amd64.tar.gz admin@server:~/

# Option B: From a mirror (example)
wget https://ghproxy.com/https://github.com/MetaCubeX/mihomo/releases/latest/download/mihomo-linux-amd64.tar.gz
```

Extract and install:
```bash
tar xzf mihomo-linux-amd64.tar.gz
mkdir -p ~/.config/mihomo
sudo cp mihomo /usr/local/bin/
```

## Step 2: Create Config

Save to `~/.config/mihomo/config.yaml`. See `templates/mihomo-config.yaml` for a minimal working template.

Key points:
- Set `geox-url.mmdb: ""` to prevent GeoIP download hang (see Pitfall below)
- Remove all `GEOIP` rules — they require the database
- Use `mode: global` with a `url-test` auto group for reliability

## Step 3: The GeoIP Pitfall (Critical)

**This is the #1 reason mihomo hangs on startup behind GFW.**

Without `geox-url.mmdb: ""`, mihomo tries to download MaxMind GeoIP database from GitHub/CDN on startup. The download hangs forever because GitHub is blocked. The proxy never starts, creating a deadlock.

**Solution:** Always include `geox-url` with empty values to skip downloads. Also remove any `GEOIP` rules from the rules section.

## Step 4: Run mihomo

```bash
# Via Hermes terminal with background=true
kill $(pgrep mihomo) 2>/dev/null; sleep 1
mihomo -f ~/.config/mihomo/config.yaml
```

## Step 5: Verify

```bash
# Check process
pgrep mihomo

# Check port
ss -tlnp | grep 7897

# Test proxy
curl -x http://127.0.0.1:7897 -s -o /dev/null -w '%{http_code}' \
  --connect-timeout 10 https://github.com
# Expected: 200

# Debug mode if needed
curl -x http://127.0.0.1:7897 --connect-timeout 10 -v https://github.com 2>&1 | tail -20
```

## Step 6: Set Environment Variables

Create `~/.proxy_env.sh`:
```bash
export HTTP_PROXY=http://127.0.0.1:7897
export HTTPS_PROXY=http://127.0.0.1:7897
export http_proxy=http://127.0.0.1:7897
export https_proxy=http://127.0.0.1:7897
export NO_PROXY=localhost,127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,.local,.internal
```

Add to `.bashrc`:
```bash
echo 'source ~/.proxy_env.sh' >> ~/.bashrc
```

## curl_cffi Proxy Format

Unlike `requests` which accepts `os.environ` or dict arguments, `curl_cffi` (used by `jmcomic` library and independently for Cloudflare bypass) has a specific proxy format:

```python
# ✅ CORRECT — pass a dict
from curl_cffi import requests
resp = requests.get(url, proxies={"http": "...", "https": "..."}, ...)

# ❌ WRONG — string causes AttributeError: 'str' object has no attribute 'get'
resp = requests.get(url, proxies="http://127.0.0.1:7897", ...)
```

### curl_cffi TLS Errors Through Proxy

When using `curl_cffi` with `impersonate` through a mihomo proxy pointing to CDN-masked VMess nodes (servername: gw.alicdn.com), Cloudflare-protected sites frequently fail with `curl: (35) TLS connect error` or `OPENSSL_internal:invalid library (0)`.

**Diagnosis**: The TLS handshake through the proxy tunnel fails because:
1. The CDN inspects inner TLS SNI after decryption
2. curl_cffi's impersonation layer has compatibility issues with certain proxy tunnel implementations

**Solutions** (in priority order):
1. Bypass the web frontend entirely and use the site's backend API directly (e.g., jmcomic's `/album/{id}` API endpoint)
2. Try different `BROWSER_VERSION` values: `"chrome120"`, `"chrome110"`, `"firefox120"`, `"safari17_0"`
3. Try without proxy if the server has direct internet access
4. Switch to SOCKS5 proxy: `curl --socks5-hostname 127.0.0.1:7897`
5. Use standard `requests` library with `urllib3` proxy (loses impersonation but may succeed on non-Cloudflare API endpoints)

---

## Using Playwright Through Proxy

```bash
pip install playwright
playwright install chromium
```

Install system deps if headless shell fails:
```bash
sudo apt-get install -y libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
  libgbm1 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
  libpango-1.0-0 libcairo2 libasound2t64 libnspr4 libnss3
```

Python usage:
```python
browser = await p.chromium.launch(
    headless=True,
    proxy={"server": "http://127.0.0.1:7897"},
    args=["--no-sandbox", "--disable-setuid-sandbox", "--ignore-certificate-errors"]
)
```

**Pitfall:** GitHub and similar sites detect headless browsers and redirect to `chrome-error://chromewebdata/`. When this happens, use `wait_until="domcontentloaded"` to avoid waiting for blocked assets, or abandon browser automation in favor of curl + API.

### Scraping JS-Rendered Pages

For Next.js/React SPA sites that render empty HTML, use Playwright with `wait_until="networkidle"` and `page.inner_text("body")` to extract visible text content after hydration. Example:

```python
await page.goto(url, wait_until="networkidle", timeout=60000)
await page.wait_for_timeout(3000)  # let dynamic content settle
text = await page.inner_text("body")
```

This works even when individual form inputs aren't findable — extract the full visible text and parse it.

## Shell Heredoc / Escaping Pitfall

When writing files to the cloud server via SSH heredocs, shell metacharacters cause corruption. **Don't fight escaping in nested quotes** — write files locally and scp them up:

```bash
# ❌ DON'T — backticks, ${}, {} all cause shell syntax errors
ssh admin@server "cat > file.py << 'EOF' ... ${var} ... EOF"

# ✅ DO — write locally, scp up
write_file /tmp/file.py → scp /tmp/file.py admin@server:/path/
```

This applies to: Python scripts with f-strings, YAML configs, HTML/CSS with template literals.

## YAML Config Editing — Never Use sed

Editing mihomo's `config.yaml` with `sed -i` **always corrupts YAML structure**. The config has nested blocks where deleting a parent key leaves orphaned children, causing `ParserError: expected <block end>, but found '<block mapping start>'`.

```bash
# ❌ Never: sed corrupts YAML nesting
sed -i '/^external-controller/d' config.yaml   # leaves orphan children!

# ✅ Always: use Python or copy from known-good template
python3 -c "
import yaml
with open('config.yaml') as f:
    cfg = yaml.safe_load(f)
cfg.pop('external-controller-cors', None)   # removes parent + children
with open('config.yaml', 'w') as f:
    yaml.dump(cfg, f)
"
```

## Large File Download Limitations

Some airport/proxy nodes impose bandwidth limits that cause downloads >10MB to timeout (curl exit code 28 or 35). Small requests (GitHub API, HTML pages) work fine. **Workarounds by priority**:

| Approach | Works? |
|----------|--------|
| `git clone --depth 1` (source, small) | ✅ Fast — compile from source if needed |
| `wget` with `--timeout=300` | ⚠️ May still fail |
| User downloads binary locally, SCP to server | ✅ Always — user's PC has better proxy |
| `pip install` large packages | ⚠️ Often times out, try background mode |

### ⚠️ GitHub Release Asset Downloads (Specific Domain Failure)

`release-assets.githubusercontent.com` is a separate domain from `github.com` and `api.github.com`. It frequently fails with TLS errors both through proxy AND direct connection, while API calls and git clone succeed.

**Diagnosis**: If `curl -x http://127.0.0.1:7897 https://github.com` returns 200 but `curl -L https://github.com/USER/REPO/releases/download/v1.0/file.tar.gz` fails with `SSL_ERROR_SYSCALL` (exit 35), the issue is the release CDN domain specifically. This can happen even with `--insecure` / `--no-check-certificate`.

**Test direct connection too** — on some servers, `release-assets.githubusercontent.com` fails even without proxy due to the system's GnuTLS version being incompatible with Azure CDN's TLS configuration:
```bash
# Proxy test
curl -x http://127.0.0.1:7897 -L -o /dev/null <release-url>  # Likely: exit 35
# Direct test  
curl --noproxy '*' -L -o /dev/null <release-url>  # May also: exit 35 or super slow
# API calls work fine
curl -x http://127.0.0.1:7897 https://api.github.com/repos/USER/REPO/releases/latest  # 200 OK
```

**Multi-tool matrix** (all fail on release-assets CDN if system GnuTLS is the root cause):
| Tool | Proxy | Direct | Notes |
|------|-------|--------|-------|
| curl | ❌ exit 35 | ❌ exit 35 or ~10KB/s | |
| wget | ❌ TLS error | ❌ same | |
| Python requests | ❌ SSL EOF | ❌ same | verify=False doesn't help |
| aria2c -x16 | ❌ TLS | ❌ TLS handshake failure | Multi-connection doesn't bypass TLS |
| `git clone` SSH | ✅ Works | ✅ Works | SSH key-based, bypasses TLS entirely |

**Workaround**: 
1. `git clone git@github.com:USER/REPO.git` via SSH — always works, bypasses TLS (small source code only)
2. If the project is Python: clone source + `pip install -r requirements.txt` — no need for the release binary
3. User downloads the binary on local PC → `scp` to server
4. NEVER use QQ file transfer for binaries — QQ wraps files in a non-extractable format (PK header but not valid zip/tar)

**When all downloads fail**: ask the user to download the file on their local PC and SCP it to the server. QQ file attachments are unreliable for binary files.

If the proxy works for GitHub but **fails for YouTube, Twitter/X, iwara.tv** (TLS handshake killed with `SSL_ERROR_SYSCALL` after Client Hello), the issue is likely **double filtering**:

1. **CDN filtering**: If your VMess nodes use `servername: gw.alicdn.com` (Alibaba CDN SNI masking), the CDN inspects inner TLS SNI and drops adult/social media traffic.
2. **Cloud provider DPI**: Chinese cloud providers (Aliyun, Tencent) run Deep Packet Inspection at the datacenter egress, detecting and dropping TLS flows to sensitive sites even through encrypted tunnels.

### Diagnostic Checklist

```
1. Test DIRECT (--noproxy '*'): TCP timeout → GFW blocked
2. Test via proxy (--socks5-hostname): SOCKS5 granted, TLS fails → CDN/DPI filtering
3. GitHub works but site X doesn't → CDN is inspecting inner SNI, not full block
4. All sites fail equally → proxy node is dead or config broken
```

### Workarounds

| Approach | Feasibility |
|----------|------------|
| Switch to Reality/Hysteria2 protocol | Airport-dependent |
| Switch to overseas VPS (non-Chinese cloud) | $5/month |
| Use Web Search (Tavily/DDGS) as indirect access | Easy, free tier — see `references/hermes-web-search.md` |
| Download on local PC, transfer to server | Free, always works |

### Site Accessibility Matrix (for gw.alicdn.com CDN proxies)

| Category | Accessible | Blocked |
|----------|-----------|---------|
| Developer | GitHub, PyPI, npm | — |
| Video | Bilibili, Douyin (direct) | YouTube, iwara.tv |
| Social | — | Twitter/X, Facebook |
| Adult | — | iwara.tv, R18 sites |
| Chinese | All domestic sites (direct) | — |

## Git GnuTLS Pitfall — SSH Workaround

**Symptom:** `git clone/push` through HTTP proxy fails with `gnutls_handshake() failed: The TLS connection was non-properly terminated`, while `curl -x http://127.0.0.1:7897` to the same URL succeeds (HTTP 200).

**Root cause:** Git on Debian/Ubuntu is compiled with **GnuTLS** as its TLS backend (not OpenSSL). GnuTLS's TLS handshake is incompatible with some cloud/VPS proxy nodes, even though the HTTP CONNECT tunnel establishes successfully. curl uses OpenSSL which works fine.

**Check SSL backend:**
```bash
git -c http.sslBackend=openssl clone https://example.com/repo.git 2>&1
# If: "Unsupported SSL backend 'openssl'. Supported SSL backends: gnutls"
# → confirmed GnuTLS-only build
```

**Fix: Use SSH protocol through SOCKS5 proxy**

1. Generate an SSH key and add to GitHub:
```bash
ssh-keygen -t ed25519 -C "you@github" -f ~/.ssh/id_ed25519 -N ""
# Add ~/.ssh/id_ed25519.pub to https://github.com/settings/ssh/new
```

2. Configure git to use SSH + SOCKS5 proxy:
```bash
git config --global core.sshCommand "ssh -o ProxyCommand='nc -X 5 -x 127.0.0.1:7897 %h %p'"
```

Or per-repo:
```bash
git clone [ssh://git@github.com/user/repo.git](ssh://git@github.com/user/repo.git)  # auto-uses sshCommand
```

3. Verify:
```bash
ssh -o ProxyCommand="nc -X 5 -x 127.0.0.1:7897 %h %p" -T git@github.com
# Expected: "Hi <user>! You've successfully authenticated..."
```

**Note:** `nc -X 5` specifies SOCKS5. The mihomo `mixed-port` (7897) supports SOCKS5 natively.

On headless servers, run mihomo as a `systemd --user` service for auto-start:

```bash
mkdir -p ~/.config/systemd/user ~/.config/mihomo

cat > ~/.config/systemd/user/mihomo.service << 'EOF'
[Unit]
Description=Mihomo Proxy (Clash Meta)
After=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/mihomo -f %h/.config/mihomo/config.yaml
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

sudo loginctl enable-linger $USER
systemctl --user daemon-reload
systemctl --user enable --now mihomo
```

### Config Location for User Service

User systemd services can't read `/etc/mihomo/` (root-owned). Copy config to `~/.config/mihomo/`:

```bash
sudo cp /etc/mihomo/config.yaml ~/.config/mihomo/config.yaml
sudo chown $USER:$USER ~/.config/mihomo/config.yaml
```

### Remove GUI-Specific Keys (Headless)

Configs exported from GUI clients (Clash Verge) contain Windows-specific keys that crash on Linux:

```python
# Use Python to clean — sed corrupts YAML
with open('config.yaml') as f:
    lines = f.readlines()
out = []
skip = False
for line in lines:
    if 'external-controller-pipe' in line:
        continue
    if 'external-controller-cors' in line:
        skip = True
        continue
    if skip:
        if line.startswith(' ') or line.startswith('\\t'):
            continue
        skip = False
        out.append(line)
    else:
        out.append(line)
open('config.yaml','w').write(''.join(out))
```

⚠️ Never use `sed` to edit mihomo YAML — block-level deletions easily orphan child keys.

## Common Issues

| Symptom | Cause | Fix |
|---------|-------|-----|
| Startup hangs, log shows "Can't find MMDB, start download" | GeoIP download blocked | Set geox-url.mmdb to empty |
| YAML parse error after sed edit | `sed` left orphaned child keys | Use Python to remove parent+children together |
| User service exits code=1 | Config at `/etc/mihomo/` not readable by user | Copy to `~/.config/mihomo/` |
| `external-controller-pipe` parse error | Windows GUI key in Linux config | Remove the key (see Python script above) |
| CONNECT tunnel OK but TLS handshake fails | Airport CDN filters site / Cloud DPI | See "Double Filtering" section above |
| `git clone/push` fails with `gnutls_handshake() failed` | Git compiled with GnuTLS, which is incompatible with some proxy nodes | Switch to SSH protocol + SOCKS5 proxy (see "Git GnuTLS Pitfall" below) |
| curl returns 000, exit code 35 | SSL/TLS through proxy fails | Check node alive with `nc -zv host port` |
| mihomo runs but port not listening | Config parse error | Run with `-d /tmp` for debug |
| Playwright page.goto HTTPS timeout | Headless detected by GitHub/Cloudflare | Use `wait_until="domcontentloaded"`, longer timeout, or switch to curl+API |
| systemd user service exits code=1 | Config file in root-owned dir (e.g. /etc/mihomo/) | Copy config to ~/.config/mihomo/config.yaml and use -f %h/.config/mihomo/config.yaml in ExecStart |
| systemd user service exits code=1 with YAML parse error | Config corrupted by sed/awk edits | NEVER use sed on YAML. Use Python to parse → modify → dump (see below) |
| Config works as root but fails as user service | GUI-specific keys (external-controller-pipe, external-controller-cors) in config | Remove these keys: they contain Windows paths and cause YAML parse errors on headless Linux |

### YAML Config Editing: Never Use sed (Critical)

sed/awk will corrupt YAML indentation — deleting a parent key leaves orphaned children, producing cryptic parse errors like "did not find expected key" or "expected <block end>, but found '<block mapping start>'".

**Correct approach — use Python:**

```bash
python3 << 'PYEOF'
import yaml
with open('/home/admin/.config/mihomo/config.yaml') as f:
    config = yaml.safe_load(f)

# Remove GUI-specific keys (Windows-only, cause parse errors on headless)
for key in ['external-controller-pipe', 'external-controller-cors']:
    config.pop(key, None)

with open('/home/admin/.config/mihomo/config.yaml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
print('Config sanitized OK')
PYEOF
```

This pattern applies to any YAML config editing (mihomo, hermes config.yaml, docker-compose, etc.). Parse in Python, modify the dict, dump back. Never sed.

### User Systemd Service Pitfall

When running mihomo as a **user systemd service** (not root), the config file must be in a user-writable directory. If you try to use /etc/mihomo/config.yaml (root-owned, mode 600), the service crashes with status=1/FAILURE and no clear error. Fix: sudo cp /etc/mihomo/config.yaml ~/.config/mihomo/config.yaml && sudo chown $USER: ~/.config/mihomo/config.yaml, then use ExecStart=/usr/local/bin/mihomo -f %h/.config/mihomo/config.yaml.

Systemd user service template:
```ini
[Unit]
Description=Mihomo Proxy (Clash Meta)
After=network-online.target

[Service]
Type=simple
ExecStart=/usr/local/bin/mihomo -f %h/.config/mihomo/config.yaml
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
```

## References

- `references/sms-platforms.md` — SMS verification platform research and pricing (接码平台)
- `templates/mihomo-config.yaml` — Minimal working config template
