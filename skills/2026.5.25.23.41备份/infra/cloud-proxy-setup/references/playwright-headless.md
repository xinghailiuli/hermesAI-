# Playwright Headless Browser on Cloud Servers

Setting up Playwright with Chromium on a headless Ubuntu cloud server, using the mihomo proxy.

## System Dependencies

Chromium requires these libraries on Ubuntu 24.04 (headless server):

```bash
sudo apt-get install -y libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
  libgbm1 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
  libpango-1.0-0 libcairo2 libasound2t64 libnspr4 libnss3
```

## Install Playwright

```bash
pip install playwright

# Install Chromium (requires proxy if server can't reach Microsoft CDN)
export HTTP_PROXY=http://127.0.0.1:7897 HTTPS_PROXY=http://127.0.0.1:7897
playwright install chromium
```

## Proxy Configuration in Playwright

```python
from playwright.async_api import async_playwright

PROXY = {"server": "http://127.0.0.1:7897"}

browser = await p.chromium.launch(
    headless=True,
    proxy=PROXY,
    args=["--no-sandbox", "--disable-setuid-sandbox", "--ignore-certificate-errors"]
)
```

## Gotchas

### HTTPS page timeouts with vmess proxies
vmess nodes have 300-1000ms latency. Pages with many assets (GitHub, CDN-heavy sites) will timeout with default `wait_until="load"`.

**Fix**: Use `wait_until="domcontentloaded"` and increase timeout:
```python
await page.goto(url, wait_until="domcontentloaded", timeout=60000)
```

### GitHub headless detection
GitHub detects headless Chromium and returns `chrome-error://chromewebdata/` even with a working proxy. The form fills, then the next page is blocked. GitHub uses aggressive anti-bot measures (Arkose Labs CAPTCHA) that cannot be bypassed in headless mode.

**Verdict**: Do NOT attempt headless GitHub registration. Have the user register manually.

### Dynamic SPA login pages (Next.js/React)
Some sites (e.g., 5sim.net signin) render forms dynamically via React hydration. Buttons found by `data-testid` or text selectors may be in the DOM but **not visible** (hidden behind mobile menus, off-screen, or not yet hydrated).

**Fix**: Navigate directly to the sign-in URL instead of clicking UI buttons:
```python
# BAD: clicking a button that's in DOM but not visible
signin_btn = page.locator('[data-testid="go-to-sign-in"]').first
await signin_btn.click()  # Timeout: element not visible

# GOOD: go directly to the known URL
await page.goto("https://5sim.net/signin", wait_until="domcontentloaded")
```

Also, for React SPAs, form inputs may not be findable by standard selectors until after hydration completes. Increase `wait_for_timeout(3000)` after navigation before querying inputs.

### `--no-sandbox` is required
On cloud servers without a desktop environment, Chromium needs `--no-sandbox` and `--disable-setuid-sandbox`.

### Verification: HTTP works, HTTPS fails
If `http://httpbin.org/ip` returns 200 but `https://github.com` times out, the proxy is correctly configured — the issue is vmess node latency + HTTPS page weight. Use `domcontentloaded` strategy.

## Minimal Test Script

```python
async with async_playwright() as p:
    browser = await p.chromium.launch(headless=True, proxy=PROXY, args=ARGS)
    page = await browser.new_page()
    resp = await page.goto("http://httpbin.org/ip", timeout=15000)
    print(resp.status)  # Should be 200
```
