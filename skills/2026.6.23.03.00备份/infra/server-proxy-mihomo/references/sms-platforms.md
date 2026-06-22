# SMS Verification Platforms (接码平台)

## Current Status (2026-05)

| Platform | Status | Notes |
|----------|--------|-------|
| **sms-activate.org** | ❌ Shut down | Closed Dec 2025, recommends HeroSMS |
| **5sim.net** | ✅ Active | Best option. JWT API, Chinese UI, supports 500+ services |
| **HeroSMS (hero-sms.com)** | ⚠️ Unverified | 403 from our server, may need special access |

## 5sim Setup & Authentication

**Website is Next.js SPA** — login form renders client-side. Playwright works for scraping but extracting the token requires the web UI.

### Getting the API Token

1. Register/login at https://5sim.net/signin via browser
2. Go to Settings → API
3. Copy the JWT token (valid 1 year, format: `eyJhbGciOiJSUzUxMi...`)
4. Use in requests: `Authorization: Bearer <token>`

### API Endpoints

Base URL: `https://5sim.net/v1`

Key endpoints:
- `GET /v1/user/profile` — check balance, user info
- `GET /v1/guest/products` — list all services + prices (public)
- `GET /v1/guest/countries` — list countries (public)

The `/v1/guest/products?country=china` and similar filtered endpoints may return 404 — use the unfiltered `/v1/guest/products` and filter locally.

### Check Balance

```bash
curl -s "https://5sim.net/v1/user/profile" -H "Authorization: Bearer <token>"
# Returns: {"id":..., "email":..., "balance":1.94, ...}
```

## 5sim Pricing (China Services)

Prices in USD for activation (one-time SMS):

| Service | Price | RMB |
|---------|-------|-----|
| bilibili | $0.02 | ~¥0.14 |
| baidu | $0.02 | ~¥0.14 |
| weibo | $0.02 | ~¥0.14 |
| zhihu | $0.10 | ~¥0.70 |
| xianyu (闲鱼) | $0.13 | ~¥0.90 |
| xhsapp (小红书) | $0.26 | ~¥1.80 |
| taobao | $0.01 | ~¥0.07 |
| alipay | $0.01 | ~¥0.07 |
| didi | $0.03 | ~¥0.20 |
| dingtalk | $0.06 | ~¥0.42 |
| toutiao (头条) | $0.09 | ~¥0.63 |

## Key Notes

- Minimum top-up: ~$1 (supports Alipay/WeChat)
- Token: JWT, valid 1 year, found in Settings → API
- Number rental: 5-30 min per activation
- Auto-refund if no SMS received within window
- Sites: https://5sim.net (EN), https://5sim.net/zh/ (CN)
- The website itself doesn't need proxy from China — it's on non-blocked servers
