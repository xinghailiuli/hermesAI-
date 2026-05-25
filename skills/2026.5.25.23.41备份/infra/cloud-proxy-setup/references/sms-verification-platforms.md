# SMS Verification Platforms (接码平台)

Reliable platforms for purchasing temporary phone numbers to receive SMS verification codes. Useful for automating account registrations on Chinese services (B站, 微博, 贴吧, etc.) from cloud servers.

## Platform Status (May 2026)

| Platform | Status | API | Notes |
|----------|--------|-----|-------|
| **5sim.net** | ✅ Active | JWT Bearer | Best option. Supports B站, 微博, 百度, 知乎, 淘宝, 支付宝, 京东, etc. |
| **sms-activate.org** | ❌ Shut Down | — | Ceased operations December 2024. Recommends HeroSMS. |
| **HeroSMS** (hero-sms.com) | ⚠️ 403 | — | Returns 403 from Chinese cloud servers (possibly GFW block). |

## 5sim Details

### Pricing (USD, China numbers)

| Service | Price | Notes |
|---------|-------|-------|
| B站 (bilibili) | $0.02 | ~¥0.14 |
| 微博 (weibo) | $0.02 | ~¥0.14 |
| 百度 (baidu) | $0.02 | ~¥0.14 |
| 知乎 (zhihu) | $0.10 | ~¥0.70 |
| 淘宝 (taobao) | $0.01 | ~¥0.07 |
| 支付宝 (alipay) | $0.01 | ~¥0.07 |
| 小红书 (xhsapp) | $0.26 | ~¥1.80 |
| 闲鱼 (xianyu) | $0.13 | ~¥0.90 |
| 大麦 (damai) | $0.82 | ~¥5.70 (expensive!) |

### Authentication

5sim uses **JWT tokens** (valid 1 year). The token is NOT obtained via email/password API — it's found in the web UI:

1. User registers on https://5sim.net (requires email verification)
2. Logs in via web browser
3. Goes to Settings → API
4. Copies the JWT token

The signin page is a Next.js SPA — the login form is dynamically rendered and hard to automate with Playwright. Don't attempt headless login; have the user get the token from their own browser.

### API Usage

```bash
# All authenticated requests use Bearer token
curl -s "https://5sim.net/v1/user/profile" \
  -H "Authorization: Bearer $5SIM_TOKEN" \
  -H "Accept: application/json"

# Check balance
curl -s "https://5sim.net/v1/user/profile" \
  -H "Authorization: Bearer $5SIM_TOKEN" \
  -H "Accept: application/json" | jq '.balance'

# Get prices for a service
curl -s "https://5sim.net/v1/guest/prices?country=china&product=bilibili"
```

### Key API Endpoints

- `GET /v1/user/profile` — balance, account info
- `GET /v1/guest/prices?country=china&product=<name>` — pricing
- `POST /v1/user/buy/activation/...` — purchase a number
- `GET /v1/user/check/<order_id>` — check for received SMS
- Refer to https://5sim.net/docs for full API reference

### Minimum Top-Up

$1 minimum. The website lists pricing in USD, but **Alipay is supported** — pay in CNY at the real-time exchange rate (≈¥7.2 per USD). Also supports WeChat, Visa/Mastercard, and USDT.

### Number Availability

Numbers come from various countries (Russia, Philippines, Indonesia, etc.) but work for Chinese services. The `country=china` parameter works for some services but not all — try `country=any` if china returns empty results.

## Automation Flow

```
1. Get 5SIM_TOKEN from user's Settings → API page
2. Check balance: curl /v1/user/profile
3. Buy number: POST /v1/user/buy/activation/<country>/<operator>/<service>
4. Poll for SMS: GET /v1/user/check/<order_id> every 5 seconds
5. Extract code from SMS body
6. Fill code into target registration form via Playwright
7. Finish order: POST /v1/user/finish/<order_id>
```

Note: If no SMS arrives within 5-30 minutes, 5sim auto-cancels and refunds.
