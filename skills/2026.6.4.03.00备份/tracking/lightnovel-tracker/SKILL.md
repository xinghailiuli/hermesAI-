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

**Behind a proxy** (e.g. mihomo on `127.0.0.1:7897`): TLS handshake through the
proxy can take 15–30s. Use extended timeout and pass the proxy explicitly:

```bash
curl -s -L --connect-timeout 15 --max-time 45 \
  -x http://127.0.0.1:7897 \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  "https://www.lightnovel.cn/" -o /tmp/ln_home.html
```

If the proxy is slow to establish, retry once before falling back to `--noproxy '*'`
(which reaches Cloudflare directly but may then fail on the follow redirect to
`lightnovel.fun`).

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
  - Has **full metadata**: author in brackets `[作者]`, explicit timestamps, hit counts
  - Stale: shows featured/ranked content, lags 7+ days behind latest uploads in observed sessions
- **items** array: `{id:N, type:N, title:"...", action_params:N, pic_url:"...", ...}`
  - Has **newer content** (higher aid numbers) but **no author, no explicit timestamp**, no description
  - Each `pic_url` contains `t=<unix_epoch>` — the CDN cover-image upload timestamp, a reliable proxy for publish date
  - items without `pic_url` timestamps: fall back to aid-number heuristic (higher = newer)

Entry URLs follow the pattern: `https://www.lightnovel.cn/cn/article/{aid}`

## Step 3 — Extract timestamps and filter

### For ranks entries (explicit `time` field)
- Parse `time` fields, filter for entries within the desired window (e.g. last 3 days)
- `time` format: `"YYYY-MM-DD HH:MM:SS"` — use `datetime.strptime()`

### For items entries (no explicit time field)
Items lack a `time` field but their `pic_url` carries a CDN timestamp:

```python
t_match = re.search(r'[?&]t=(\d+)', pic_url)
if t_match:
    ts = int(t_match.group(1))
    if 1000000000 < ts < 2000000000:  # Valid Unix epoch (2001–2033)
        cdn_time = datetime.fromtimestamp(ts)
```

The `t=` value is a Unix epoch second — the cover image upload time, which closely approximates the article publish date. Treat it as the entry date for filtering.

If `pic_url` has no valid timestamp (e.g. `t=8000000000` is a static placeholder), fall back to the aid-number heuristic: recent average is ~8–14 aids/day, so estimate `date ≈ last_known_date + (aid - last_known_aid) / 10 days`.

### Filtering
- Filter out 国产网文 (Chinese web novels): look for Japanese author names in brackets like `[西条阳]`, `[白井ムク]`, or Korean `[최지인]`
- Items array has no author info — cross-reference with known series or check title patterns (isekai themes, JP naming conventions) to distinguish JP/KR from CN
- Disambiguation heuristics (see `references/title-parsing.md` for regex patterns):
  - Kana in author bracket → 日轻; Hangul → 韩轻
  - Pure kanji in brackets within category 3/106 → almost always 日轻
  - No brackets at all (items array) → treat as 日轻 by default in this category

### Extract author and volume
Use the patterns in `references/title-parsing.md` to:
- Strip `[作者]` from titles for author attribution
- Detect volume numbers, chapter markers, and completion status from title text

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
- **Stale ranks vs fresh items**: The `ranks` array is curated/featured content — can lag 7+ days behind. The `items` array carries newer entries but with less metadata. Check BOTH arrays and merge results. The items array often contains the only entries within a 3-day recency window
- **Items array is cumulative across sessions**: The SSR `items` array persists the same entries across multiple days (entries from 05-27 were still present on 06-01). Do NOT assume all items are recent — ALWAYS validate each item's CDN timestamp. Items migrate to the `ranks` array over time (observed: aid=1144581 in items on 05-29, moved to ranks by 06-01), but items are never removed from the items array within the observed ~10-entry window
- **Items lack author metadata**: Items entries have only `id`, `type`, `title`, `action_params` (aid), `pic_url`, `group_id`, `comments`, `hits`. No author field, no description. Supplement author info from known series or cross-reference with ranks entries that share the same aid
- **No timestamps on items — use CDN timestamps**: The `items` array lacks explicit `time` fields. Extract the `t=<unix_epoch>` from `pic_url` as the primary dating method. Validate: timestamps in range 1e9–2e9 are valid Unix epochs; `t=8000000000` and similar static values are placeholders — discard them and fall back to aid-number heuristic
- **JS object literal, not JSON**: The NUXT state is a JS expression, not valid JSON. Use regex extraction, not `json.loads()`
- **Cloudflare on .us domain**: `lightnovel.us` requires JS challenge, curl won't work
- **SPA-only routes**: Only `/` is SSR'd. `/cn/article/{aid}` returns 404 with empty state. Content is loaded client-side after auth
- **Proxy-induced timeouts**: In environments behind a local proxy (e.g. mihomo on `127.0.0.1:7897`), TLS handshake through the proxy can take 15–30 seconds. Use `--connect-timeout 15 --max-time 45` and pass the proxy explicitly with `-x http://127.0.0.1:7897`. Direct connection (`--noproxy '*'`) will reach Cloudflare but receive a 301 redirect to `lightnovel.fun` which may then fail behind the same proxy

## Reference files

- `references/api-and-architecture.md` — Full API endpoint catalog, NUXT parameter mapping, webpack chunk analysis, and data structure documentation
- `references/cdn-timestamps-and-dating.md` — CDN timestamp extraction technique, aid-to-date linear correlation data from observed sessions, items-vs-ranks comparison with field-by-field breakdown. Includes cross-session items persistence analysis and migration tracking
- `references/title-parsing.md` — Regex patterns for extracting author (from `[作者]` brackets) and volume/chapter info from title strings. Includes JP/KR/CN disambiguation heuristics and items-array fallback notes.

## Output format

When reporting to the user, use a compact table format in Chinese.

**Default format** (3+ entries in window):

```
## 📚 轻之国度 · 日轻/韩轻翻译区

| # | 书名 | 作者 | 卷数 | 更新时间 | 链接 |
|---|------|------|------|----------|------|
| 1 | **书名** | 作者 | 第N卷 | MM-DD | [aid=N](url) |
```

**Sparse window format** (≤2 entries in window — common on weekends or slow periods):
Use a sectioned report with three tiers to give the user useful context even when the target window is thin:

```
## 📚 轻之国度 · 日轻/韩轻翻译区 更新报告

**抓取时间**：… | **数据来源**：… | **筛选窗口**：…

### 🆕 最近N天新增/更新（X本）
[Table of in-window entries]

### ⚠️ 刚超出窗口（N天前，Y本）
[Table of entries 1-2 days outside window — the closest misses]

### 📊 本周其余活跃更新（日期范围）
[Table of slightly older entries for broader context]
```

Key rules:
- Only include 日轻/韩轻 (Japanese/Korean LN), exclude 国产网文
- Author names in brackets `[作者]` are the original JP/KR author
- Volume info when available ("第N卷", "（上/下）", "已完结", "至第N话", "完")
- Links use `https://www.lightnovel.cn/cn/article/{aid}` format
- If nothing found in the window, state clearly and show the closest recent entries
- When running as a cron job, the sectioned format is always preferred because the user cannot ask follow-ups — give them the full picture in one message
- For volume/author parsing regex patterns, see `references/title-parsing.md`
