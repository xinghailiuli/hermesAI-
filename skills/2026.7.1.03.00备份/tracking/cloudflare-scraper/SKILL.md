---
name: cloudflare-scraper
description: >-
  Scrape Cloudflare-protected doujin/manga sites (禁漫天堂/jmcomic, nhentai, etc.)
  using curl_cffi impersonation and direct API access. Covers proxy setup,
  TLS fingerprint spoofing, API auth token generation, and fallback strategies
  when Cloudflare blocks the request.
---

# Cloudflare Comic/Manga Site Scraper

Scrape doujin/manga sites protected by Cloudflare using TLS fingerprint spoofing
with `curl_cffi` or direct API access.

## Triggers

- User asks to find/access a "车牌号" (album ID) on jmcomic/18comic/nhentai
- Any task requiring scraping a Cloudflare-protected comic or image site
- User provides a Python script using `curl_cffi` for Cloudflare bypass

---

## Prerequisites

```bash
pip install curl_cffi jmcomic  # --break-system-packages if needed
```

The `jmcomic` library already depends on `curl_cffi`, so installing jmcomic pulls
it in automatically.

---

## Approach A: Direct API Access (jmcomic)

禁漫天堂 has a REST API backend that can be accessed directly with proper auth headers.
This bypasses the Cloudflare web frontend entirely.

### Step 1 — Install jmcomic

```bash
pip install jmcomic --break-system-packages
```

### Step 2 — Generate auth tokens

The jmcomic API uses `token` and `tokenparam` headers generated from timestamps:

```python
from jmcomic import JmCryptoTool, time_stamp

ts = time_stamp()
token, tokenparam = JmCryptoTool.token_and_tokenparam(ts)
```

### Step 3 — Set up request headers

```python
headers = {
    "Accept-Encoding": "gzip, deflate",
    "User-Agent": "Mozilla/5.0 (Linux; Android 9; V1938CT Build/PQ3A.190705.11211812; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/91.0.4472.114 Safari/537.36",
    "token": token,
    "tokenparam": tokenparam,
    "Accept": "application/json, text/plain, */*",
}
```

### Step 4 — Query album endpoint

```python
import requests
resp = requests.get(f"https://www.cdnutc.me/album/{album_id}", headers=headers, timeout=10)
data = resp.json()  # {"code": 200, "data": [...]} or {"code": 200, "data": []}
# Empty data array means the album ID does not exist
```

### Step 5 — Search with encrypted response

The search API returns encrypted data:

```python
resp = requests.get(f"https://www.cdnutc.me/search?q={keyword}", headers=headers, timeout=10)
from jmcomic import JmApiResp
decrypted = JmApiResp(resp, ts)
result = decrypted.json()  # still contains encrypted data string in 'data' field
```

### Domain discovery

The jmcomic library auto-discovers working API domains at startup via `/setting`:
```json
GET https://www.cdnutc.me/setting
→ {"code":200,"data":{"version":"1.8.2","jm3_version":"2.0.26","ipcountry":"CN"}}
```

Domains that have been seen working:
- `www.cdnhjk.net` (Cloudflare)
- `www.cdngwc.cc` (Cloudflare)
- `www.cdngwc.net` (Cloudflare)
- `www.cdngwc.club` (Cloudflare)
- `www.cdnutc.me` ✅ (no Cloudflare, works from Chinese servers)

If other domains fail TLS, use `cdnutc.me` directly.

---

## Approach B: curl_cffi Cloudflare Bypass

For sites behind Cloudflare that don't have a backend API (like nhentai).

### Step 1 — Basic setup

```python
from curl_cffi import requests

PROXY_URL = "http://127.0.0.1:7897"  # or None if direct connection works
BROWSER_VERSION = "chrome120"

proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}
```

### Step 2 — Make request

```python
response = requests.get(
    target_url,
    headers=headers,
    proxies=proxies,
    impersonate=BROWSER_VERSION,
    timeout=15
)
```

### Step 3 — Interpret status codes

| Code | Meaning |
|------|---------|
| 200 | Success — page retrieved |
| 404 | Album/ID does not exist on this platform |
| 403, 503 | Still blocked by Cloudflare — try different proxy node or browser version |

---

## Pitfalls

### 1. curl_cffi `proxies` parameter must be a dict

```python
# ✅ CORRECT
proxies = {"http": "http://127.0.0.1:7897", "https": "http://127.0.0.1:7897"}

# ❌ WRONG — causes AttributeError: 'str' object has no attribute 'get'
proxies = "http://127.0.0.1:7897"
```

### 2. TLS errors through proxy (exit 35)

If `curl_cffi` reports `curl: (35) TLS connect error`:
- Try without proxy (`PROXY_URL = None`) if the server has direct internet access
- Try different `BROWSER_VERSION` values: `"chrome120"`, `"chrome110"`, `"firefox120"`, `"safari17_0"`
- The proxy node itself may be blocking or filtering the target site's SNI
- The `servername` SNI mask (e.g., `gw.alicdn.com`) used by VMess proxies clashes with Cloudflare-facing sites
- Switch to direct API access (Approach A) if available

### 3. Proxy does not route certain sites — diagnostic

With mihomo/Clash proxies using CDN SNI masking (e.g., `servername: gw.alicdn.com`):
- nhentai.net, 18comic.vip, pornhub, iwara.tv are frequently blocked by CDN-level filtering
- Google, YouTube, Twitter may also be blocked depending on the proxy

**Critical diagnostic**: verify the proxy is actually routing traffic:
```bash
# Expected: a foreign IP (e.g. US/HK/JP)
# If it returns the SERVER'S OWN IP (e.g. 47.108.235.219), the proxy isn't routing
curl -x http://127.0.0.1:7897 https://httpbin.org/ip
```

Even with `mode: global` in mihomo config, many VMess proxies with SNI masking silently fail on TLS for Cloudflare-protected sites. The proxy itself connects, but the CDN tunnel breaks. In this case:
- Use direct API access (Approach A) for jmcomic — the `cdnutc.me` domain works without proxy
- For nhentai/etc., try socks5 proxy (`--socks5-hostname`) instead of HTTP CONNECT

### 3a. Proxy config can have rules blocking certain sites

Check the mihomo/clash config for rules that may interfere:
```bash
cat ~/.config/mihomo/config.yaml | grep -E "^(proxy-groups|rules|proxies)" -A 5
```

Common patterns that block scraping:
- `DOMAIN-KEYWORD,<site>,REJECT` — blocks traffic entirely
- No matching rule → falls through to `MATCH,<proxy-group>` which may itself fail on certain CDNs

### 4. 356448-style "车牌号" may not be a jmcomic album ID

If the API returns `{"code":200,"data":[]}`, the ID simply does not exist on jmcomic.
It might be:
- An nhentai gallery ID (which also uses numeric IDs but has different numbering)
- A color hex code coincidentally matching the pattern
- A product SKU or model number
- From a different platform entirely

### 5. Encrypted search responses

jmcomic search results are AES-encrypted. Use `JmApiResp` to decrypt, but even decrypted
data may be further encoded. This is a limitation of the search API — album detail queries
(via `/album/{id}`) return plain JSON.

### 6. Proxy format for curl_cffi vs requests

| Library | Proxy format |
|---------|-------------|
| `requests` (stdlib) | `{"http": "...", "https": "..."}` |
| `curl_cffi` | `{"http": "...", "https": "..."}` (same as requests) |
| `jmcomic` (internal) | Set via config YAML under `client.postman.meta_data.proxies` |

### 7. Web frontend domains are more heavily protected

The 18comic.vip web frontend uses Cloudflare's most aggressive protection.
The API backend (cdnutc.me) has much weaker protection and is the preferred access method.

## 下载 GitHub Release APK/Assets

When downloading APKs or large release assets from behind the GFW, use `ghproxy.net`:

```bash
# Single file via ghproxy (Chinese CDN mirror)
curl -L "https://ghproxy.net/https://github.com/{owner}/{repo}/releases/download/{tag}/{filename}" -o output.apk

# Recommended: aria2c for speed (8 parallel connections, resume support)
aria2c -x 8 -s 8 -k 1M \
  --max-tries=5 --connect-timeout=15 --timeout=120 \
  --continue=true -d /tmp -o filename.apk \
  "https://ghproxy.net/https://github.com/{owner}/{repo}/releases/download/{tag}/{filename}"
```

**Key wrinkle**: GitHub redirections from `github.com` to CDN `release-assets.githubusercontent.com` often fail behind GFW + proxy. The `ghproxy.net` mirror handles:
- Rewriting to Chinese-accessible Azure CDN nodes
- Following the redirect chain to the actual Azure blob
- Fast multi-threaded download to Chinese servers

### Verify APK downloaded correctly

```bash
# Check file type
file /tmp/downloaded.apk  # Should say "Android package (APK)"
# Check it's a valid ZIP (APK = ZIP format)
unzip -l /tmp/downloaded.apk | head -10
# File size should match the GitHub release metadata
ls -lh /tmp/downloaded.apk
```

## GitHub API Search Tips

When searching GitHub for comic tools, the GitHub API search may return 0 results with certain token configurations:

```bash
# If fine-grained token lacks search scope, use anonymous API (rate-limited)
# But anonymous API may also return empty for sensitive keywords

# Preferred: use `curl` directly against github.com without token
curl -s "https://api.github.com/search/repositories?q=jmcomic+android&sort=stars"
```

**Token formats:**
- `ghp_*` — classic token (usually has search scope)
- `github_pat_*` — fine-grained token (may lack search scope; check repo access)
- Anonymous — rate-limited (10 req/min) but often works

**Diagnostic test:**
```bash
# Token is valid
curl -s "https://api.github.com/user" -H "Authorization: Bearer $TOKEN"
# Search works
curl -s "https://api.github.com/search/repositories?q=test&per_page=1" -H "Authorization: Bearer $TOKEN"
```

## 禁漫天堂 APK GitHub 项目

| 项目 | Stars | 说明 |
|------|-------|------|
| [hect0x7/JMComic-APK](https://github.com/hect0x7/JMComic-APK) | ★5,350 | 官方原版 APK，含 GitHub Actions 构建发布 |
| [Tom6814/JMComic3-APK-NO-Ads](https://github.com/Tom6814/JMComic3-APK-NO-Ads) | ★68 | 去广告版、去游戏版、修复版 |
| [niuhuan/jenny](https://github.com/niuhuan/jenny) | ★1,116 | 跨平台漫画浏览器，支持 Android/iOS/PC |
| [deretame/Breeze](https://github.com/deretame/Breeze) | ★1,622 | Flutter 多源漫画阅读器（禁漫/哔咔/ehentai 等） |
| [Dedicatus546/jm-mobile](https://github.com/Dedicatus546/jm-mobile) | ★40 | Jetpack Compose 原生 Android 客户端 |
| [ComicSparks/jasmine](https://github.com/ComicSparks/jasmine) | ★5,286 | 跨平台漫画浏览器（含禁漫源） |

**最新版 APK 直链（v2.0.26）:**
```
国内加速: https://ghproxy.net/https://github.com/hect0x7/JMComic-APK/releases/download/2.0.26/2.0.26.apk
GitHub直链: https://github.com/hect0x7/JMComic-APK/releases/download/2.0.26/2.0.26.apk
```

## 参考

- jmcomic Python 库: https://github.com/hect0x7/JMComic-Crawler-Python
- jmcomic-downloader (GUI): https://github.com/lanyeeee/jmcomic-downloader
- ghproxy 国内加速: https://ghproxy.net
- API 参考文档: `references/jmcomic-api.md`
- GitHub 工具列表: `references/github-tools.md`
