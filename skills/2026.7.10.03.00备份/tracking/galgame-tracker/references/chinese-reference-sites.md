# Chinese Galgame Reference Sites — Status & Notes

Last checked: 2026-07-06

## 青桔网 (qingju.net)

- **Status**: ❌ Unreachable (connection timeout, curl returns exit code 000)
- **Notes**: DNS resolves but no HTTP response. Possibly down or behind aggressive firewall.

## Hikarinagi (hikarinagi.org) — was hikarinagi.com

- **Status**: ✅ Reachable (HTTP 301 from .com → .org, Cloudflare + Nuxt.js SPA)
- **HTTP**: 301 → 200 OK (Cloudflare + Nuxt)
- **Architecture**: Nuxt.js SPA behind Cloudflare — all endpoints return the same HTML shell with CSS. Content is loaded client-side.
- **Title**: "Hikarinagi - 一个ACGN文化社区"
- **Domain change**: hikarinagi.com redirects to hikarinagi.org; use hikarinagi.org directly.
- **API attempts**:
  - `/api/` → returns SPA shell (404)
  - `/api/v1/articles` → returns SPA shell (404)
  - `/sitemap.xml` → returns SPA shell
  - `/feed` → returns SPA shell
  - `api.hikarinagi.com` → NXDOMAIN (no separate API subdomain)
- **Potential approach**: Check homepage HTML for `window.__NUXT__` SSR state (same technique as lightnovel-tracker skill). The Nuxt.js architecture means the initial page load may embed data. This hasn't been verified yet.
- **Recommendation**: VNDB API is the primary source. Hikarinagi is supplementary — log in via browser for human review, not automated scraping.

## NekoGAL (nekogal.com)

- **Status**: ❌ Unreachable (connection timeout)
- **Notes**: Same as 青桔网 — DNS resolves but no HTTP response.

## TouchGal (touchgal.net)

- **Status**: ⚠️ Returns HTTP 403 Forbidden
- **Notes**: The server is alive but blocks automated access. May require browser user-agent, cookies, or Cloudflare bypass.

## Summary

None of the Chinese reference sites are currently suitable for automated cron-job scraping. VNDB API remains the only reliable programmatic data source for Galgame release tracking. Steam store pages are a viable supplementary source for Chinese descriptions of Chinese-original games when VNDB lacks them.
