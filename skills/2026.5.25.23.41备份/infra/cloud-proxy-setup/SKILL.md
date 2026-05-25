---
name: cloud-proxy-setup
description: Install and configure mihomo (Clash Meta) proxy on Chinese cloud servers that cannot reach GitHub or foreign sites. Covers the chicken-and-egg bootstrap problem, geodata pitfalls, and QQ-attachment config ingestion.
category: infra
---

# Cloud Server Proxy Setup (Mihomo/Clash Meta)

Bootstraps a working proxy on an Alibaba Cloud ECS or similar Chinese server where GitHub and foreign sites are blocked by the GFW.

## Trigger Conditions

- Server cannot `curl https://github.com` (times out or connection refused)
- Server cannot access proxy subscription URLs (proxyinfo.net etc.)
- Need to install tools that only exist on GitHub
- User has a Clash subscription but no proxy client installed on the server

## Prerequisites

- User's Clash subscription config (`.yaml` file or pasted content)
- The config MUST include `mixed-port` (or `port`/`socks-port`)
- Subscription config obtained from user's phone/PC Clash client via export

---

## Step-by-Step

### 1. Get the subscription config from the user

The server cannot reach the subscription URL (chicken-and-egg). Get the config directly:

```
User's Clash client → Export/Share → Copy to clipboard → Send via QQ as .txt attachment
```

The config lands in `~/.hermes/cache/documents/doc_*_qqdownloadftnv5`. Find it:
```bash
find ~/.hermes/cache/documents -name "doc_*" -mmin -5
```

### 2. Save and sanitize the config

```bash
mkdir -p ~/.config/mihomo
cp <found_path> ~/.config/mihomo/config.yaml
sed -i 's/\r$//' ~/.config/mihomo/config.yaml   # CRLF → LF (QQ files use Windows line endings)
```

Note the `mixed-port` value (or `port`/`socks-port`) from the config — this is the proxy port to use later.

### 3. Install mihomo kernel

GitHub is blocked, so use **ghproxy.net mirror**:

```bash
# Find latest version
curl -sL --max-time 15 "https://ghproxy.net/https://github.com/MetaCubeX/mihomo/releases/latest" | grep -oP 'v[0-9]+\.[0-9]+\.[0-9]+' | head -1

# Download (adjust version as needed)
curl -sL --max-time 60 "https://ghproxy.net/https://github.com/MetaCubeX/mihomo/releases/download/v1.19.4/mihomo-linux-amd64-compatible-v1.19.4.gz" -o /tmp/mihomo.gz

# Install
cd /tmp
gunzip -f mihomo.gz
chmod +x mihomo
sudo mv mihomo /usr/local/bin/mihomo
```

Verify: `mihomo -v`

### 4. ⚠️ CRITICAL: Disable geodata auto-download

**Without this step, mihomo hangs forever.** The geodata files (Country.mmdb, geoip.dat) are hosted on GitHub — which is blocked.

#### Quick fix (may not work if config has GEOIP rules)

Add to config.yaml near the top:

```yaml
geodata-mode: false
geox-url:
  mmdb: ""
  geoip: ""
  geosite: ""
```

#### The real fix: strip all GEOIP-dependent content

> ⚠️ **`geodata-mode: false` is NOT enough.** If the config contains ANY `GEOIP,…` or `GEOSITE,…` rules, mihomo WILL try to download MMDB regardless of `geodata-mode`. The log will show:

```
level=info msg="Can't find MMDB, start download"
```

And mihomo hangs indefinitely trying to fetch it from GitHub. The only reliable fix is to **create a minimal config** that removes:
- All `GEOIP,…` and `GEOSITE,…` rules
- All `GEOIP` entries from `rules:` section
- Any `geosite:` references in DNS fallback filters

Only `domain`-based rules (`DOMAIN,`, `DOMAIN-SUFFIX,`, `DOMAIN-KEYWORD,`, `MATCH,`) are safe — they don't trigger MMDB downloads.

See `references/minimal-config.yaml` for a working template.

### 5. Start mihomo with debug logging (first run)

On first run, use debug logging to verify health checks pass:

```bash
mihomo -f ~/.config/mihomo/config.yaml 2>&1 | tee /tmp/mihomo.log &
```

Wait 5 seconds, then check health:
```bash
sleep 5 && grep "Health Checked" /tmp/mihomo.log
```

You should see lines like:
```
Health Checked, proxy: 🇯🇵 日本1, alive: true, delay: 317 ms
Health Checked, proxy: 🇺🇸 美国1, alive: true, delay: 873 ms
```

If nodes show `alive: false, delay: 65535`, they're unreachable. The `url-test` group (`Auto`) will automatically pick a healthy node.

Once confirmed working, switch to `log-level: info` and restart:
```bash
sed -i 's/log-level: debug/log-level: info/' ~/.config/mihomo/config.yaml
# restart mihomo
```

Verify the port is listening:
```bash
ss -tlnp | grep <port>    # e.g. 7897
```

### 6. Test the proxy

```bash
# Quick test
curl -sI --max-time 10 -x http://127.0.0.1:<PORT> https://github.com

# Verbose test (shows CONNECT tunnel negotiation)
curl -x http://127.0.0.1:<PORT> --connect-timeout 10 -v https://github.com 2>&1 | head -20
```

Expected output:
```
* Connected to 127.0.0.1 (127.0.0.1) port <PORT>
* CONNECT tunnel: HTTP/1.1 negotiated
> CONNECT github.com:443 HTTP/1.1
< HTTP/1.1 200 Connection established
* CONNECT phase completed
```

If you see `SSL_ERROR_SYSCALL` after the CONNECT tunnel is established, possible causes (in order):
1. **Node is dead/unreachable** — check mihomo debug logs for health check results (`alive: false`)
2. **Airport content filtering** — many Chinese commercial airports (especially 性价比机场) block adult/gambling/niche categories at the node level. GitHub works but iwara.tv fails = airport filtering. Try different node locations; if all fail, the airport doesn't allow that category. Switch airports.
3. **TLS fronting blocked** — the `servername` (e.g., `gw.alicdn.com`) may be flagged or blocked by the CDN.

### Airport content filtering diagnostic flow

When a specific site fails through proxy but other sites work:

1. **Confirm the CONNECT tunnel establishes:** `curl -x http://127.0.0.1:<PORT> -v https://<site> 2>&1 | grep "Connection established"` — if 200, the proxy accepted the request and established a TCP tunnel to the target.

2. **Isolate TLS from TCP — test HTTP first:** `curl --socks5-hostname 127.0.0.1:<PORT> --proxy-insecure http://<site> -v 2>&1 | head -5`. If `> GET / HTTP/1.1` appears, TCP works — the problem is specifically TLS. If HTTP also fails, the node can't reach the site at all (dead node or GEOIP block).

3. **Inspect the TLS handshake with openssl:** `echo "Q" | openssl s_client -connect <site>:443 -proxy 127.0.0.1:<PORT> -servername <site> -tls1_2 2>&1 | head -30`. Key signals:
   - `"SSL handshake has read 39 bytes and written 279 bytes"` → server sent a TLS Alert (reject) after Client Hello. The CDN filtered based on SNI.
   - `"no peer certificate available"` + `"Cipher is (NONE)"` → TLS was never established. CDN-level block.
   - If you see `"Certificate chain"` and a cipher → TLS succeeded, the issue is elsewhere.

4. **If CDN filtering is confirmed:** check the proxy's `servername` field. Many Chinese airports use `servername: gw.alicdn.com` (Alibaba CDN) for SNI masking. This CDN inspects inner-TLS SNI and blocks adult/gambling/niche categories regardless of whether the node itself allows them. On Windows (SChannel TLS stack), the same config may work because the TLS fingerprint differs enough to avoid CDN inspection — this explains "same nodes work on PC but not on server" scenarios.

5. **Try different transport:** some CDN frontends inspect TCP-streamed TLS but not WebSocket-encapsulated traffic. Adding `network: ws` + `ws-opts: {path: /}` to the VMess proxy config MAY bypass content inspection (not guaranteed — the server must support ws transport).

6. Try the same site on multiple nodes (🇯🇵/🇺🇸/🇸🇬/🇭🇰) — if ALL fail, it's airport-level filtering.

6b. **Cloud DPI check**: Have the user test the SAME site from their home PC through the SAME proxy nodes. If their PC can access the site but the server can't, the problem is NOT the airport — it's the cloud provider's datacenter DPI (especially common on Alibaba Cloud ECS). See Pitfalls section for protocol upgrade options.

7. Try direct connection (without proxy): `curl --noproxy '*' --connect-timeout 5 https://<site>` — if this also fails, GFW is blocking too.

### 7. Make it permanent

```bash
echo 'export HTTP_PROXY=http://127.0.0.1:<PORT>' >> ~/.bashrc
echo 'export HTTPS_PROXY=http://127.0.0.1:<PORT>' >> ~/.bashrc
```

For systemd-based auto-start, use the template at `templates/mihomo.service`.

---

## Troubleshooting

### mihomo starts but port not listening → check geodata
The #1 cause. mihomo tries to download geodata files from GitHub on first run. Set `geodata-mode: false` in config.

### Config file has CRLF line endings
QQ attachments on Windows use `\r\n`. mihomo may choke. Fix: `sed -i 's/\r$//' config.yaml`

### Config from phone app has `allow-lan: false`
This is fine for server use (only localhost needs the proxy). The proxy listens on 127.0.0.1 only.

### ghproxy.net times out for some files
The mirror has rate limits and doesn't cache all releases. Try a different version number or use `wget --timeout` with retries.

### "Connection refused" for GitHub even after proxy is up
Check that `geodata-mode: false` was actually applied and mihomo was restarted after the change.

---

## Pitfalls

- **Don't try to curl the subscription URL from the server** — it's blocked. Get config from the user directly.
- **Chinese cloud providers have their own DPI** — Alibaba Cloud, Tencent Cloud, etc. deploy datacenter-level Deep Packet Inspection that can block TLS traffic to foreign restricted sites (adult, Google services, social media) even when the traffic passes through a working proxy tunnel. This is NOT the airport filtering — it's the cloud provider's infrastructure. If the user can access the same site from their home broadband through the same proxy nodes but the server can't, suspect cloud DPI first. Switching airports won't fix this; you need either an overseas VPS, a different protocol (Reality/Hysteria2), or fall back to domestic alternatives.
- **Chinese domestic sites work without proxy** — Bilibili, Douyin, iXigua, Tencent Video, Youku, and other Chinese platforms are directly accessible from Chinese cloud servers with zero proxy configuration. yt-dlp has excellent support for 哔哩哔哩. Always test domestic equivalents before concluding a video download task is impossible.
- **TLS fingerprint matters** — Windows SChannel and Linux OpenSSL produce different TLS Client Hello fingerprints. Chinese cloud DPI and CDN frontends may pass traffic that looks like a Windows browser but block Linux OpenSSL fingerprints (perceived as proxy/VPN traffic). This explains why the same proxy config works on the user's PC but fails on the server.
- **Protocol upgrade can bypass DPI** — VMess+TLS with CDN SNI masking (gw.alicdn.com) is vulnerable to DPI inspection. VLESS+Reality (masquerades as real website TLS) and Hysteria2 (QUIC/UDP, harder to inspect) are stronger against cloud DPI. If the airport supports these protocols, switching may resolve DPI blocks.
- **Phone Clash apps generate valid configs** — the same subscription works across all clients.
- **The proxy port in config might differ from env vars already set** — always check the actual config file for `mixed-port`, don't assume 7890.
- **`pip install mihomo` is a different thing** — it's a Honkai Star Rail library, not the Clash Meta kernel.
- **ghproxy.net for downloads, NOT for registration flows** — it's a read-only file mirror, can't POST to GitHub signup.
- **Headless browsers (Playwright/Selenium) get blocked by GitHub** — even with a working proxy, GitHub returns `chrome-error://chromewebdata/` or redirects to CAPTCHA for headless Chromium. Do NOT try to automate GitHub registration; have the user register manually on their phone/PC.
- **Playwright proxy works for HTTP but HTTPS may time out** — the vmess nodes have >300ms latency, so HTTPS pages with many assets can exceed default timeouts. Use `wait_until="domcontentloaded"` and increase timeout to 60s.

## References

- `references/minimal-config.yaml` — Zero-geodata config template that avoids the MMDB download hang
- `references/playwright-headless.md` — Playwright headless Chromium setup on cloud servers: system deps, proxy config, timeout workarounds, and GitHub anti-bot caveats
- `references/sms-verification-platforms.md` — 接码平台现状 (5sim, sms-activate已死): 定价, JWT认证, API端点, 自动化流程
- `references/github-token-setup.md` — GitHub PAT token 配置: 获取、验证、git credentials 存储、环境变量持久化
- `references/ai-coding-tools.md` — AI coding tools ecosystem: CodeGraphContext, github-to-mcp, github-mcp-server, search patterns for GitHub MCP discovery
- `references/airport-filtering-deep-dive.md` — Airport filtering diagnostic flow
- `references/chinese-video-platforms.md` — 国内视频站可访问性速查: B站/抖音/西瓜/腾讯/优酷 直连状态与 yt-dlp 用法
