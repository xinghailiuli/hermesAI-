# jmcomic (禁漫天堂) API Reference

## Library

- **PyPI**: `jmcomic` v2.7.0
- **GitHub**: [hect0x7/JMComic-Crawler-Python](https://github.com/hect0x7/JMComic-Crawler-Python)
- **Dependencies**: curl_cffi, pillow, pycryptodome, commonx, pyyaml

## Installation

```bash
pip install jmcomic --break-system-packages
```

The `jmcomic` package path may be in `~/.local/lib/python3.12/site-packages/`.

## API Domains

Auto-discovered at startup via `/setting` endpoint. Current working domains (June 2026):

| Domain | Cloudflare | Notes |
|--------|-----------|-------|
| `www.cdnhjk.net` | ✅ Yes | Blocked from Chinese servers |
| `www.cdngwc.cc` | ✅ Yes | Blocked from Chinese servers |
| `www.cdngwc.net` | ✅ Yes | Blocked from Chinese servers |
| `www.cdngwc.club` | ✅ Yes | Blocked from Chinese servers |
| `www.cdnutc.me` | ❌ No | ✅ Works from Chinese servers |

## Auth Token Generation

```python
from jmcomic import JmCryptoTool, time_stamp

ts = time_stamp()
token, tokenparam = JmCryptoTool.token_and_tokenparam(ts)
# Output: token = "3ecebff8de7568ef0002ad0e344a8e70"
#         tokenparam = "1782694389,2.0.26"
```

The token is an MD5 hash of `ts + secret`. Default secret is `18comicAPP` (from `JmMagicConstants.APP_TOKEN_SECRET_1`).

## API Endpoints

### GET /setting
Returns server version and client IP country:
```json
{"code":200,"data":{"version":"1.8.2","jm3_version":"2.0.26","ipcountry":"CN"}}
```

### GET /album/{id}
Returns album metadata:
```json
{"code":200,"data":[...]}  // or {"code":200,"data":[]} if not found
```
Empty `data` array means the album ID does not exist.

### GET /search?q={keyword}
Returns encrypted search results. Data is AES-encrypted and must be decrypted:
```python
from jmcomic import JmApiResp
resp = requests.get(url, headers=headers)
decrypted = JmApiResp(resp, ts)
result = decrypted.json()  # 'data' field still contains encoded content
```

## Library API (high-level)

```python
from jmcomic import JmOption

# Default config (reads from internal default YAML)
option = JmOption.default()

# Create client
client = option.new_jm_client()

# Get album detail
detail = client.get_album_detail("356448")
# detail.title, detail.author, detail.tags, detail.series
```

## Proxy Configuration

The default config includes proxy settings:
```yaml
client:
  postman:
    type: curl_cffi
    meta_data:
      proxies:
        https: "127.0.0.1:7897"
        http: "127.0.0.1:7897"
```

To configure without proxy, create a custom YAML config:
```yaml
client:
  domain: []
  postman:
    type: requests
    meta_data: {}
  impl: api
  retry_times: 3
```

Note: Setting `impl: api` uses `RequestsPostman` instead of `CurlCffiPostman`.

## Manual API Calling (requests-based, bypassing jmcomic curl_cffi)

When the jmcomic library's internal `curl_cffi` has TLS issues in proxy environments,
use raw `requests` with the `cdnutc.me` domain directly:

```python
import requests
from jmcomic import JmCryptoTool, time_stamp

ts = time_stamp()
token, tokenparam = JmCryptoTool.token_and_tokenparam(ts)

headers = {
    "Accept-Encoding": "gzip, deflate",
    "User-Agent": "Mozilla/5.0 (Linux; Android 9; V1938CT Build/PQ3A.190705.11211812; wv) AppleWebKit/537.36",
    "token": token,
    "tokenparam": tokenparam,
}

# Album detail query — empty data = ID does not exist
resp = requests.get(
    f"https://www.cdnutc.me/album/{album_id}",
    headers=headers, timeout=10
)

# Search — returns AES-encrypted data
resp = requests.get(
    f"https://www.cdnutc.me/search?search_query={keyword}&main_tag=0&page=1",
    headers=headers, timeout=10
)
from jmcomic import JmApiResp
jmresp = JmApiResp(resp, ts)
model_data = jmresp.model_data  # decrypted
# redirect_aid = exact match, content = fuzzy results
```

### Proxy config for custom YAML

```yaml
client:
  domain: [jmapi: www.cdnutc.me]
  postman:
    type: requests        # ← use requests, not curl_cffi
    meta_data: {}
  impl: api
  retry_times: 3
```

Note: the jmcomic library auto-updates its domain list from the `/setting` endpoint
at startup, which may override `client.domain`. For pure manual API calling, skip
the YAML config and use `requests` directly as shown above.

## Search API specifics

- The `search_query` parameter in the URL is the keyword to search
- `main_tag=0` means search all categories
- `page` is 1-indexed
- The response `redirect_aid` field indicates an exact match (when present, `content` is empty)
- Encrypted search responses require `JmApiResp` for decryption

## Token Auth Detail

The token is an MD5 hash of `ts + secret`. Default secret is `18comicAPP` (from `JmMagicConstants.APP_TOKEN_SECRET_1`).
Token has a limited lifespan (timestamp-based) — regenerate on each session.

## mihomo 代理排坑

### 代理出口 IP 验证
通过代理访问 `https://httpbin.org/ip`，检查返回的 IP 是否为代理节点 IP（而非服务器本机 IP）。
如果返回服务器本机 IP，说明代理配置未生效。

### 常见 TLS 错误
- `curl: (35) TLS connect error` / `OPENSSL_internal:invalid library` — 代理节点与目标服务器的 TLS 协商失败，通常需要更换节点
- `SSL: UNEXPECTED_EOF_WHILE_READING` — 目标服务器断连，GFW 阻断或 Cloudflare 拦截
- 某些 vmess 节点对特定 CDN（Cloudflare、AWS CloudFront）有兼容问题

### 代理节点切换
当默认节点失效时，可通过修改 mihomo config.yaml 中的 `proxy-groups[].proxies` 顺序或通过
external-controller API 切换。如果没有启用 external-controller，需要手动编辑 config.yaml 并重启 mihomo。

## Known Limitations

- The `JmOption.new_jm_search_client()` method does NOT exist (as of v2.7.0). Search is done via manual API calls.
- The library auto-updates domain list from the `/setting` endpoint on every instantiation, overriding manual domain config.
- Token auth is required for API requests. Without valid `token`/`tokenparam` headers, requests may return 403.
- API returns `{"code":200,"data":[]}` for non-existent IDs — this does NOT mean the ID is always invalid (search may still return a `redirect_aid` for the same ID)
