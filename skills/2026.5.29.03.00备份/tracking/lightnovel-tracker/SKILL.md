---
name: lightnovel-tracker
description: >
  Scrape 轻之国度 (lightnovel.cn) for latest Japanese/Korean light novel
  translation updates. Covers SSR NUXT-state extraction, API endpoint
  discovery from webpack chunks, and known site architecture constraints.
  Also documents the general technique for scraping Nuxt.js SPAs via
  embedded `window.__NUXT__` state.
---

# 轻之国度 (LightNovel.cn) Tracker

Scrape https://www.lightnovel.cn for the latest Japanese/Korean light novel
translation posts. The site is a Nuxt.js SPA with auth-gated APIs, so the primary
data source is the homepage SSR `__NUXT__` state.

## Triggers

- Cron job or user asks to check lightnovel.cn for new translations
- Any task involving scraping a Nuxt.js SPA site via SSR state

## Step 1 — Fetch homepage and extract NUXT state

```bash
curl -s -L --max-time 30 \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  "https://www.lightnovel.cn/" -o /tmp/ln_home.html
```

The HTML contains a `<script>` with the SSR state:

```js
window.__NUXT__=(function(a,b,c,...){return {layout:"default",data:[{...}]}}(0,1,...));
```

The function parameters are positional: `a=0, b=1, c="url", d="", e=2, f=13, ...`
Values in the data object are single-letter references to these params.

## Step 2 — Parse NUXT data to extract light novel entries

Use regex to extract the data object:

```python
nuxt_match = re.search(
    r'window\.__NUXT__=\(function\([^)]+\)\{return (\{.*?)(?:;)?\}\((.*?)\)\);</script>',
    html, re.DOTALL
)
data_str = nuxt_match.group(1)   # The JS object literal
params_str = nuxt_match.group(2)  # The comma-separated argument values
```

### Map parameters

```python
func_params = "a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,z,A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z,_,$,aa,ab,ac,ad,ae,af,ag".split(',')
raw_params = params_str.split(',')
param_map = dict(zip(func_params, raw_params))
# Resolve: strip quotes, unescape \u002F → /, \u003D → =, etc.
```

### Find the light novel section

The light novel section has `more_params:"3,106,1"` (fid=3, typeid=106).
Find it by locating this string in the data, then extract the enclosing `{...}` block.

### Extract entries

- **ranks** array: `{rank:N, aid:N, title:"...", cover:"...", comments:N, hits:N, time:"YYYY-MM-DD HH:MM:SS", ...}`
- **items** array: `{id:N, type:N, title:"...", action_params:N, ...}` — no timestamp in items

Entry URLs follow the pattern: `https://www.lightnovel.cn/cn/article/{aid}`

## Step 3 — Filter and report

- Parse `time` fields, filter for entries within the desired window (e.g. last 3 days)
- Items array entries have no time field — use aid numbers as a heuristic (higher = newer)
- Filter out 国产网文 (Chinese web novels): look for Japanese author names in brackets like `[西条阳]`, `[白井ムク]`, or Korean `[최지인]`

## Known API endpoints (auth required)

Discovered from webpack chunk `b4bd28379f024a47d9fd.js`. All return `{"code":4,"message":404}` without login session:

| Endpoint | Purpose |
|---|---|
| `/api/recom/get-pc-home` | Homepage data (used for SSR) |
| `/api/recom/get-ranks` | Rankings |
| `/api/category/get-article-by-cate` | Articles by category (the one we need) |
| `/api/category/get-article-cates` | Article categories |
| `/api/category/get-categories` | Categories list |

## Site architecture

- **Domains**: `lightnovel.cn` → redirects to `lightnovel.fun`; `lightnovel.us` is behind Cloudflare JS challenge
- **Routes**: `/cn/article/{aid}`, `/cn/forum/{gid}`, `/cn/themereply/{id}`
- **SSR**: Only the homepage (`/`) is SSR-rendered. All other routes return the SPA shell with empty NUXT data and HTTP 404 status
- **gid mapping**: `13` = 轻小说 (light novel), `12` = 资讯 (news), etc.
- **Article types**: `cover_type: 0` = text, `cover_type: 1` = image/cover

## Pitfalls

- **Auth wall**: APIs require a login session. The homepage SSR is the only public data source
- **Stale data**: Homepage shows "featured/ranked" entries, not the full chronological list. Most recent entries may not appear on the homepage for days
- **No timestamps on items**: The `items` array in each section lacks time fields. Only `ranks` has them
- **JS object literal, not JSON**: The NUXT state is a JS expression, not valid JSON. Use regex extraction, not `json.loads()`
- **Cloudflare on .us domain**: `lightnovel.us` requires JS challenge, curl won't work
- **SPA-only routes**: Only `/` is SSR'd. `/cn/article/{aid}` returns 404 with empty state. Content is loaded client-side after auth

## Reference files

- `references/api-and-architecture.md` — Full API endpoint catalog, NUXT parameter mapping, webpack chunk analysis, and data structure documentation

## Output format

When reporting to the user, use a compact table format in Chinese:

```
## 📚 轻之国度 · 日轻/韩轻翻译区

| # | 书名 | 作者 | 卷数 | 更新时间 | 链接 |
|---|------|------|------|----------|------|
| 1 | **书名** | 作者 | 第N卷 | MM-DD | [aid=N](url) |
```

Key rules:
- Only include 日轻/韩轻 (Japanese/Korean LN), exclude 国产网文
- Author names in brackets `[作者]` are the original JP/KR author
- Volume info when available ("第N卷", "（上/下）", "已完结")
- Links use `https://www.lightnovel.cn/cn/article/{aid}` format
- If nothing found in the window, state clearly and show the closest recent entries
