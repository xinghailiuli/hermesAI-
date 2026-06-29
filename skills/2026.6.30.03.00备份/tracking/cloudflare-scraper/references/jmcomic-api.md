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

## Known Limitations

- The `JmOption.new_jm_search_client()` method does NOT exist (as of v2.7.0). Search is done via manual API calls.
- The library auto-updates domain list from the `/setting` endpoint on every instantiation, overriding manual domain config.
- Token auth is required for API requests. Without valid `token`/`tokenparam` headers, requests may return 403.
