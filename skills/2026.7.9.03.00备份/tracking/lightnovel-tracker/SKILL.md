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

**Primary approach**: Try `lightnovel.fun` directly with `--noproxy '*'`. This domain
resolves to `66.94.115.188` and has consistently worked when `.cn` fails.

```bash
curl -s -L --connect-timeout 15 --max-time 45 \
  --noproxy '*' \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  "https://lightnovel.fun/" -o /tmp/ln_home.html
```

**Fallback via `.cn` domain** (may redirect to `.fun`):

```bash
curl -s -L --max-time 30 \
  -H "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36" \
  "https://www.lightnovel.cn/" -o /tmp/ln_home.html
```

**Behind a proxy** (e.g. mihomo on `127.0.0.1:7897`): TLS handshake through the
proxy can take 15–30s. Use extended timeout. If the proxy returns 502, skip it
and use `--noproxy '*'` with the `.fun` domain directly:

```bash
curl -s -L --connect-timeout 15 --max-time 45 \
  -x http://127.0.0.1:7897 \
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

### Map parameters (⚠️ comma-safe parsing required)

**Do NOT use `params_str.split(',')`** — argument values may contain commas inside nested parens/braces. Use bracket-depth tracking instead:

```python
func_params = "a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,z,A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z,_,$,aa,ab,ac,ad,ae,af,ag,ah,ai,aj,ak,al,am,an,ao,ap,aq,ar,as,at,au,av,aw,ax,ay,az".split(',')
# ⚠️ This list must cover ALL function params in the SSR. If count grows past 'az',
# extend toward 'bz' or switch to dynamic extraction from the function signature regex.

def split_args_commasafe(args_str):
    """Split comma-separated args respecting nested brackets."""
    parts = []
    current = ''
    depth = 0
    for c in args_str:
        if c == ',' and depth == 0:
            parts.append(current)
            current = ''
        else:
            if c in '([{': depth += 1
            elif c in ')]}': depth -= 1
            current += c
    if current:
        parts.append(current)
    return parts

raw_params = split_args_commasafe(params_str)
param_map = dict(zip(func_params, raw_params))
# Resolve: strip quotes, unescape \\u002F → /, \\u003D → =, etc.
```

### Find the light novel section

The light novel section has `more_params:"3,106,1"` (fid=3, typeid=106).
Find it by locating this string in the data, then extract the enclosing `{...}` block.

**Critical**: There are **two** `more_params` sections in the data — one for category 1 (news, at offset ~2377) and one for category 3/106 (LN, at offset ~7259). Always scope to the second one. Search for the literal string `more_params:"3,106,1"`.

**Finding section boundaries** — the LN section sits inside `data:[...]` as one of several category objects delimited by `},{gid:`:

```python
ln_idx = data_obj.find('more_params:"3,106,1"')
# Go backwards to find opening {
section_start = ln_idx
depth = 0
while section_start > 0:
    section_start -= 1
    c = data_obj[section_start]
    if c == '}': depth += 1
    elif c == '{':
        if depth == 0: break
        depth -= 1
```

**All `ranks:[` and `items:[` searches must be scoped to `ln_section`**, not the full data object. The full data has arrays for other categories (news, etc.) that will pollute results.

### Extract entries

- **ranks** array: `{rank:N, aid:N, title:"...", cover:"...", comments:N, hits:N, time:"YYYY-MM-DD HH:MM:SS", series_name:"...", ...}`
  - Has **full metadata**: author in brackets `[作者]`, explicit timestamps, hit counts, series_name
  - Stale: shows featured/ranked content, lags 7+ days behind latest uploads in observed sessions
  - **series_name is key for CN web novel filtering** — contains distinctive markers like `[web自翻]`
  - **Simpler parsing** — rank entries have flat structure. Find all `{rank:` positions with regex and split on them.
    ```python
    ranks_start = ln_section.find('ranks:[')
    ranks_part = ln_section[ranks_start+7:]
    rank_positions = [m.start() for m in re.finditer(r'\{rank:', ranks_part)]
    rank_positions.append(len(ranks_part))
    ```
- **items** array: `{id:N, type:N, title:"...", action_params:N, pic_url:"...", ...}`
  - Has **newer content** (higher aid numbers) but **no author, no explicit timestamp**, no description
  - Each `pic_url` contains `t=<unix_epoch>` — the CDN cover-image upload timestamp, a reliable proxy for publish date
  - items without `pic_url` timestamps: fall back to aid-number heuristic (higher = newer)
  - **Split-on-`{id:` technique** works: find all `{id:` positions with regex, split on boundaries.
  - **No series_name field** — CN filtering relies on title pattern heuristics (numbered chapters)

Entry URLs follow the pattern: `https://www.lightnovel.cn/cn/article/{aid}`

## Step 3 — Extract timestamps and filter

### For ranks entries (explicit `time` field)
- Parse `time` fields, filter for entries within the desired window (e.g. last 3 days)
- `time` format: `"YYYY-MM-DD HH:MM:SS"` — use `datetime.strptime()`
- Also extract `series_name` — needed for CN web novel filtering

### For items entries (no explicit time field)
Items lack a `time` field but their `pic_url` carries a CDN timestamp.

**Extract the items array** — use bracket-depth tracking starting from `items:[`
(the offset includes the opening `[`, so `depth` starts at 0 before it):

```python
items_start = ln_raw.find('items:[')
depth = 0
items_raw = ""
for i in range(items_start, len(ln_raw)):
    c = ln_raw[i]
    if c == '[': depth += 1
    elif c == ']':
        depth -= 1
        if depth == 0:
            items_raw = ln_raw[items_start+7:i]  # skip 'items:['
            break
```

Then split by matching `{id:` positions:

```python
item_positions = [m.start() for m in re.finditer(r'\{id:', items_raw)]
```

**Extract CDN timestamps** — always use timezone-aware datetimes (CST=UTC+8)
to match the site's timezone. Mixing naive and aware datetimes causes
`TypeError` during comparison with ranks' explicit times:

```python
from datetime import datetime, timedelta, timezone
CST = timezone(timedelta(hours=8))

t_match = re.search(r'[?&]t=(\d+)', pic_url)
if t_match:
    ts = int(t_match.group(1))
    if 1000000000 < ts < 2000000000:  # Valid Unix epoch (2001–2033)
        cdn_time = datetime.fromtimestamp(ts, tz=CST)
```

**Make ranks datetimes timezone-aware too**:
```python
dt = datetime.strptime(tm.group(1), '%Y-%m-%d %H:%M:%S').replace(tzinfo=CST)
```

The `t=` value is a Unix epoch second — the cover image upload time, which closely approximates the article publish date. Treat it as the entry date for filtering.

If `pic_url` has no valid timestamp (e.g. `t=8000000000` is a static placeholder), fall back to the aid-number heuristic: recent average is ~8–14 aids/day, so estimate `date ≈ last_known_date + (aid - last_known_aid) / 10 days`.

### Filtering — exclude Chinese web novels

Category 3/106 is labeled as 日轻/韩轻 but occasionally contains Chinese web novels (国产网文). Use multiple signals:

**Ranks array** (has `series_name`):
- Check `series_name` for CN markers: `[web自翻]`, `web自翻`
- Check bracket author against known CN author names like `灯台`
- Check for numbered-chapter titles: `\d{3,4}\.` at start of clean title

**Items array** (no `series_name`):
- Title pattern heuristics: numbered chapters (`1234.XXXXX` style)
- Cross-reference with known series or author lookup

**Disambiguation heuristics** (see `references/title-parsing.md` for regex patterns):
- Kana in author bracket → 日轻; Hangul → 韩轻
- Pure kanji in brackets within category 3/106 → almost always 日轻
- No brackets at all (items array) → treat as 日轻 by default in this category

**Fallback author lookup**: when `extract_author()` returns `None` for an items entry, consult `references/known-series-authors.md` for hardcoded series→author mappings. Use this as a supplement — note that bracket-extracted authors from ranks MAY be translator names, not original authors (see pitfall "Bracket content may be translator, not author"). When a known series has a known original author that differs from the bracket name, trust the known author.

**Unknown-author workflow**: when the series is not in known-series-authors.md, use the heuristics in `references/author-research.md` to confirm JP/KR status and identify the author. If recognized from prior knowledge, **always update both `known-series-authors.md` and the script's `KNOWN_AUTHORS` dict** so future runs benefit immediately.

### Extract author and volume

Use the patterns in `references/title-parsing.md` to:
- Strip `[译者/作者]` from titles for author attribution — note that brackets may contain either the **original author** or the **translator's name** (see Pitfalls: "Bracket content may be translator, not author")
- Detect volume numbers, chapter markers, and completion status from title text

**Author display cleanup**: After extracting the author from `[brackets]`, strip the bracket from the display title to avoid duplication like `[七星蛍] [七星蛍]班上最優秀的她...`:
```python
def clean_title(title):
    t = re.sub(r'\[.*?\]\s*', '', title).strip()
    return t
```

### CN web novel detection (canonical implementation)

`scripts/parse_and_report.py` implements `is_cn_series()`:

```python
CN_SERIES_MARKERS = [
    r'\[web自翻\]',
    r'\[web翻\]',
    r'web自翻',
]

CN_BRACKET_AUTHORS = {
    '灯台',  # 被卷入了勇者召唤事件却发现异世界很和平
}

def is_cn_series(series_name, title):
    """Detect Chinese web novel from series_name or title patterns."""
    if series_name:
        for pat_str in CN_SERIES_MARKERS:
            if re.search(pat_str, series_name):
                return True
    bracket_author = extract_author(title)
    if bracket_author and bracket_author in CN_BRACKET_AUTHORS:
        return True
    clean = re.sub(r'\[.*?\]', '', title).strip()
    if re.match(r'^\d{3,4}\.', clean):
        return True
    return False
```

## Known API endpoints (auth required)

Discovered from webpack chunk `b4bd28379f024a47d9fd.js`. All return `{"code":4,"message":404}` without login session:

| Endpoint | Purpose |
|---|---|
| `/api/recom/get-pc-home` | Homepage data (used for SSR) |
| `/api/recom/get-ranks` | Rankings |
| `/api/category/get-article-by-cate` | Articles by category |
| `/api/category/get-article-cates` | Article categories |
| `/api/category/get-categories` | Categories list |

## Site architecture

- **Primary domain**: `lightnovel.fun` (resolves to `66.94.115.188`, works directly with `--noproxy '*'`)
- **Redirect domain**: `lightnovel.cn` → redirects to `lightnovel.fun`; but SSL handshake often times out (Cloudflare IPs `104.21.85.216` / `172.67.211.107`)
- **Blocked**: `lightnovel.us` is behind Cloudflare JS challenge — unusable with curl
- **Routes**: `/cn/article/{aid}`, `/cn/forum/{gid}`, `/cn/themereply/{id}`
- **SSR**: Only the homepage (`/`) is SSR-rendered. All other routes return the SPA shell with empty NUXT data and HTTP 404 status
- **gid mapping**: `13` = 轻小说 (light novel), `12` = 资讯 (news), etc.
- **Article types**: `cover_type: 0` = text, `cover_type: 1` = image/cover

## Pitfalls

- **CN web novels in category 3/106**: Despite the category label "日轻/韩轻", Chinese web novels occasionally appear in the ranks array. They follow distinctive patterns:
  - Numbered-chapter titles like `1234.参加婚礼前的准备①`, `1238.参加婚礼前的准备⑤` — long-running CN serials
  - `series_name` containing `[web自翻]` (web self-translate) marker
  - Author names like `灯台` (Chinese-style pen name, not JP/KR)
  - The `ranks` array carries `series_name` field — always check it for CN markers. The `items` array has no `series_name`, but title-pattern heuristics (numbered chapters) can catch CN entries there too.
  - When a CN entry is the only one in the target window, report it as filtered so the user knows the system is working.

- **Auth wall**: APIs require a login session. The homepage SSR is the only public data source
- **NUXT extraction regex fragile**: The regex `r'window\.__NUXT__=\(function\([^)]+\)\{return (\{.*?\})\}\((.*?)\)\);</script>'` often fails because the data object is huge (~18KB). Instead, find `window.__NUXT__=` manually, locate `</script>` as the terminator, then use `rfind('}(')` to split the data object from the args:
  ```python
  idx = html.find('window.__NUXT__=')
  end = html.find('</script>', idx)
  nuxt = html[idx:end]
  last_close = nuxt.rfind('}(')  # boundary between DATA }(ARGS)
  ```
- **Two `more_params` sections**: The data has two category sections — category 1 (news) and category 3/106 (LN). Always search for `more_params:"3,106,1"` specifically, and scope ALL `ranks:[`/`items:[` extraction to within that section's `{...}` block only.
- **Section boundary `},{` fragility (FIXED 2026-06-30)**: Use bracket-depth tracking for section-end detection instead of `data_obj.find('},{', ln_idx)`. The old approach was unreliable — `},{` appears inside the items/ranks arrays as object separators.
- **`.cn` domain unreachable**: `lightnovel.cn` (Cloudflare IPs `104.21.85.216` / `172.67.211.107`) frequently times out on SSL handshake. Use `lightnovel.fun` directly with `--noproxy '*'`.
- **Stale ranks vs fresh items**: The `ranks` array is curated/featured content — can lag 7+ days behind. The `items` array carries newer entries but with less metadata. Check BOTH arrays and merge results.
- **Items array is cumulative across sessions**: The SSR `items` array persists the same entries across multiple days. Do NOT assume all items are recent — ALWAYS validate each item's CDN timestamp.
- **Items array extraction**: The `items:[...]` array is nested inside the LN section object. Use bracket-depth tracking for both the array boundary and object splitting.
- **Items lack author metadata**: Items entries have no author field, no description, no series_name. Supplement author info from known series or cross-reference with ranks entries that share the same aid.
- **CDN timestamp can drift ~24h into the future**: Observed CDN server clock skew. When `ts > now + 86400`, clamp the effective date based on aid ordering.
- **Timezone handling**: CDN timestamps are Unix epochs (always UTC). Use `datetime.fromtimestamp(ts, tz=CST)` for timezone-aware datetimes. Ranks' explicit `time` fields must also be made aware with `.replace(tzinfo=CST)`.
- **JS object literal, not JSON**: The NUXT state is a JS expression, not valid JSON. Use regex extraction, not `json.loads()`.
- **Proxy-induced timeouts**: Behind a local proxy (e.g. mihomo), TLS handshake can take 15–30 seconds. Use `--connect-timeout 15 --max-time 45`.
- **NUXT param count drift (FIXED 2026-07-06)**: The `PARAMS` list in `scripts/parse_and_report.py` must cover ALL function parameters in the SSR `window.__NUXT__=(function(a,b,c,...){...})` signature. In July 2026 the count grew from ~48 to 67 (beyond `ag` into `am`). When params are missing, `resolve()` raises `ValueError: invalid literal for int() with base 10: 'ak'`. Fix: extend the comma-separated string in both `scripts/parse_and_report.py` and this SKILL.md to cover up to `bz` or switch to dynamic extraction from the function signature regex.
- **Author bracket display**: After extracting author from `[brackets]` in the title, always strip the bracket from the display title with `re.sub(r'\\[.*?\\]\\s*', '', title)`. Otherwise reports show duplication.
- **Bracket content may be translator, not author**: Rank titles sometimes put the *translator's* name in brackets, not the original author. Example: `[夜凪] 森林边上的小小魔女` where "夜凪" is the translator, but the original author is 小石川うみ. The `extract_author()` function is simplistic — it grabs whatever is in `[...]`. There is no reliable way to distinguish translator brackets from author brackets in SSR data. When a known series shows a bracket name that doesn't match the known author, log it in `references/changelog.md` and suggest the correct author in the report as a note. Consider adding a `TRANSLATOR_BRACKETS` override dict to `scripts/parse_and_report.py` for documented cases where bracket = translator.

## Step 4 — Report

Use the output format below. (See `scripts/parse_and_report.py` for the canonical implementation that handles all the above steps.)

## Step 5 — Enrichment (post-run housekeeping)

After reporting, check for items-array entries that have no author (output shows `未知`). For each such entry:

1. **Identify the author**: use `references/author-research.md` heuristics, cross-reference with ranks, or apply external knowledge.
2. **Update both files**:
   - `scripts/parse_and_report.py` — add to the `KNOWN_AUTHORS` dict
   - `references/known-series-authors.md` — add to the confirmed mappings table
3. If you also discovered behavioral quirks, new pitfalls, or structural insights, add them to `references/changelog.md` and the SKILL.md Pitfalls section.

This ensures the enrichment benefit is durable across cron runs and doesn't need to be rediscovered each session.

## Reference files

- `references/api-and-architecture.md` — Full API endpoint catalog, NUXT parameter mapping, webpack chunk analysis, and data structure documentation
- `references/author-research.md` — Fallback strategies for identifying unknown items-array authors, including JP/CN keyword heuristics and a cross-session enrichment workflow
- `references/cdn-timestamps-and-dating.md` — CDN timestamp extraction technique, aid-to-date linear correlation data from observed sessions, items-vs-ranks comparison with field-by-field breakdown. Includes cross-session items persistence analysis and migration tracking
- `references/title-parsing.md` — Regex patterns for extracting author (from `[作者]` brackets) and volume/chapter info from title strings. Includes JP/KR/CN disambiguation heuristics, items-array fallback notes, `clean_title()` for display, and `CN_NUMERALS` for Chinese numeral volume detection.
- `references/known-series-authors.md` — Hardcoded lookup table mapping distinctive title substrings to confirmed authors. Use when items-array entries lack `[author]` brackets — enriches reports with known author names for recurring series.
- `references/changelog.md` — Per-session log of fixes, new author mappings, and structural changes. Keeps the main SKILL.md class-level rather than cluttered with session narratives.
- `scripts/parse_and_report.py` — Standalone CLI script: `python3 parse_and_report.py /tmp/ln_home.html --days 3 [--near-days 5] [--week-days 7]`. Does the full fetch→parse→categorize→report pipeline and prints formatted output. Use as a reference implementation or invoke directly in cron jobs.

## Output format

When reporting to the user, use Chinese. Choose format based on context:

**Cron job / one-shot delivery** (user can't ask follow-ups) — use the **list format** with bullets, which is more readable in messaging platforms than markdown tables:

```
## 📚 轻之国度 · 日轻/韩轻翻译区 更新报告

**抓取时间**：… | **数据源**：… | **窗口**：… | **目录**：[category/3/106](url)

### 🆕 最近N天（X本）

1. **书名**
   └ 作者：XXX | 卷数：第N卷 | 更新：MM-DD | [阅读](url)

### ⚠️ N~M天前（Y本）

1. **书名**
   └ 作者：XXX | 卷数：第N卷 | 更新：MM-DD | [阅读](url)

### 📊 M~W天前（Z本）
...
```

**Interactive session** (user can ask follow-ups) — use the compact table format:

```
| # | 书名 | 作者 | 卷数 | 更新时间 | 链接 |
```

**Sparse window format** (≤2 entries in window): Use the sectioned report with three tiers to give context even when the target window is thin. Include `### 🆕`, `### ⚠️` (near miss), and `### 📊` (week remainder) sections.

Key rules:
- Only include 日轻/韩轻 (Japanese/Korean LN), exclude 国产网文
- Brackets `[译者/作者]` contain either the author or translator name — strip brackets from display title; report the bracket name as-is but note known discrepancies in comments
- Volume info when available ("第N卷", "（上/下）", "已完结", "至第N话", "完")
- Links use `https://www.lightnovel.cn/cn/article/{aid}` format
- If nothing found in the window, state clearly and show the closest recent entries
- When running as a cron job, always use the sectioned list format — the user cannot ask follow-ups, give them the full picture
- For volume/author parsing regex patterns, see `references/title-parsing.md`
