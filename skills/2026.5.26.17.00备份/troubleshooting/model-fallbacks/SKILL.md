---
name: model-fallbacks
description: Workarounds when the active model lacks a feature (vision, long context, code execution). Degrade gracefully instead of failing silently.
triggers:
  - model rejects image/vision input
  - model errors on tool use
  - model features not available
---

# Model Fallback Workflows

When the active model doesn't support a feature, follow these degradation chains instead of retrying the same failing call.

## Vision / Image Viewing

When the model can't see images (common with DeepSeek, some OpenAI models, etc.):

### Fallback Chain (try in order)

1. **`vision_analyze`** — Always try first. Some providers route to an auxiliary vision model.
2. **OCR via terminal** — `tesseract` if installed: `tesseract image.jpg stdout -l chi_sim+eng`
3. **Python/PIL inspection** — `execute_code` with PIL: read dimensions, format, check if it's a screenshot
4. **Ask user to describe** — "I can't see images with this model. Can you describe what's in it, or share the text/URL instead?"
5. **Request URL alternative** — If user is showing a website/screenshot, ask for the URL so you can `curl` it directly.

### Vision via API Relay + DashScope (Best for No-Vision Models)

When the primary model (e.g. DeepSeek) lacks vision, route `vision_analyze` through an existing API relay to a vision-capable provider. This requires no new API keys or services — uses infrastructure already in place.

**Tested setup (2026.5.26):**

```bash
# API relay at 127.0.0.1:8848 with DashScope wildcard (qwen/*)
hermes config set auxiliary.vision.provider "custom:apirelay"
hermes config set auxiliary.vision.model "qwen-vl-plus"
hermes config set auxiliary.vision.base_url "http://127.0.0.1:8848/v1"
hermes config set auxiliary.vision.api_key "sk-local-apirelay-2026"
```

Also register the custom provider in `config.yaml`:

```yaml
providers:
  apirelay:
    base_url: http://127.0.0.1:8848/v1
    api_key: sk-local-apirelay-2026
    model: qwen-vl-plus
```

**Verification:**

```bash
# Send a test image through the relay
python3 -c "
import base64, struct, zlib, json, urllib.request
# Create a 20x20 red PNG
def chunk(ctype, data):
    c = ctype + data
    return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
raw = b'\x00' + bytes([255,0,0])*400
w,h=20,20
png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB',w,h,8,2,0,0,0)) + chunk(b'IDAT', zlib.compress(raw*20)) + chunk(b'IEND', b'')
b64 = base64.b64encode(png).decode()
req = urllib.request.Request('http://127.0.0.1:8848/v1/chat/completions',
    data=json.dumps({'model':'qwen-vl-plus','messages':[{'role':'user','content':[{'type':'text','text':'什么颜色？'},{'type':'image_url','image_url':{'url':f'data:image/png;base64,{b64}'}}]}],'max_tokens':10}).encode(),
    headers={'Authorization':'Bearer sk-local-apirelay-2026','Content-Type':'application/json'})
print(json.loads(urllib.request.urlopen(req,timeout=15).read())['choices'][0]['message']['content'])
"
# Expected: 红色
```

**Minimum image dimensions:** DashScope `qwen-vl-plus` requires images ≥ 10x10 pixels.

**Restart required:** Hermes gateway must be restarted for `auxiliary.vision` config changes to take effect.

### URL Alternative (Best for Screenshots of Websites)

When the user sends a **screenshot of a website** (resource list, gallery, reference sites):
- Say: "I can't see images with this model — send me the URLs directly and I'll curl them!"
- Then use `curl -sL` to fetch page titles, meta descriptions, and scrape content.
- This is faster than OCR and gets exact data.

### Chinese Network / Web Search Fallback

When web_search times out or curl to Google/Bing/DuckDuckGo fails (common from WSL/China-based networks), use **Chinese domestic websites** that have consistently low latency. See [`references/chinese-web-sources.md`](references/chinese-web-sources.md) for the full list.

Quick reference:
- **百度百科** (`baike.baidu.com/item/关键词`) — encyclopedia lookup, almost never times out
- **轻之国度** (`lightnovel.cn`) — light novel rankings/news
- **轻小说文库** (`wenku8.net`) — novel listings
- **番组计划** (`bangumi.tv`) — anime ratings/info
- Always use `-H "User-Agent: Mozilla/5.0"` in curl calls.

### Pitfalls

- Do NOT retry `vision_analyze` more than twice with the same image — the error won't change.
- `sudo apt-get install tesseract` will fail without sudo. Check with `which tesseract` first.
- PIL (`from PIL import Image`) may not be installed. Check before using in execute_code.
- Prefer URL-request over OCR when the image is clearly a website screenshot — users are usually happy to paste links instead.

## Provider Fallback Configuration

When the main model provider is unavailable (timeout, rate-limit, outage), Hermes can auto-switch to a fallback provider. See [`references/hermes-custom-provider.md`](references/hermes-custom-provider.md) for the full configuration guide, including the `hermes config set` pitfall (JSON string vs YAML) and a quick-reference table of supported providers.

## Provider Fallback (API Key Exhaustion / Rate Limit)

When the primary model provider returns **402 (Insufficient Balance)** or **429 (TPM Rate Limit)** or times out, Hermes can auto-failover to a backup provider.

### Error Codes & Meaning

| Code | Meaning | Action |
|------|---------|--------|
| **402** | Insufficient Balance — valid key but no credits | Switch model or provider; key is NOT dead, just empty |
| **429** | TPM (Tokens Per Minute) rate limit — too many requests in a short window | Wait 30-60s or switch to a different model (e.g. v4-pro → v4-flash) |
| **401** | Invalid key — wrong or revoked | Discard key, don't retry |
| **Timeout** | Provider slow/unreachable | Try fallback provider |

**Critical**: Do NOT declare a provider/model "dead" on 402 or 429. These are transient — the same key works again after top-up (402) or cooldown (429).

### Quick Model Switch (Same Provider)

When only the model variant is the problem (not the provider), switch the default model:

```bash
# Switch to v4-flash for chat (faster, lower TPM pressure)
hermes config set model.default deepseek-v4-flash

# Switch to v4-pro for coding (higher quality)
hermes config set model.default deepseek-v4-pro
```

This is faster than switching providers — same API key, different model tier.

### Setup: Add SiliconFlow as Backup Provider

Edit `~/.hermes/config.yaml` manually (do NOT use `hermes config set` — it stores values as JSON strings):
```yaml
providers:
  siliconflow:
    base_url: https://api.siliconflow.cn/v1
    api_key: sk-xxx
    model: deepseek-ai/DeepSeek-V3
fallback_providers:
  - siliconflow
```
Restart Hermes to apply. When the primary model (e.g. DeepSeek) fails with 402/timeout, Hermes auto-switches to SiliconFlow.

### Verification
```python
import requests
r = requests.post(
    "https://api.siliconflow.cn/v1/chat/completions",
    headers={"Authorization": "Bearer sk-xxx", "Content-Type": "application/json"},
    json={"model": "deepseek-ai/DeepSeek-V3", "messages": [{"role":"user","content":"hi"}], "max_tokens": 5}
)
# 200 = working, 401 = bad key, 402 = no balance
```

### Key Validation Before Configuring
Always test API keys directly with curl/requests before adding them to config:
- 401 = invalid key → discard
- 402 = valid but no balance → mark as depleted, keep for future refill
- 200 = ✅ good to use

## Long Output / Context Truncation

When model responses get cut off or the context is too large:

1. Use `delegate_task` to offload reasoning-heavy subtasks
2. Use `execute_code` to process data and return only results
3. Compress intermediate outputs with `session_search` for recall
