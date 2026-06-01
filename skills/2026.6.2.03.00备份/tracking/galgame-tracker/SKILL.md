---
name: galgame-tracker
description: >
  Fetch recent Galgame/visual novel releases using the VNDB Kana API.
  Filter for Chinese (zh-Hans/zh-Hant) and English language support.
  Output in Chinese with game name, release date, description, and cover image.
  Also covers reference sites (Hikarinagi, TouchGal) and their accessibility constraints.
---

# Galgame 新作追踪（VNDB API）

Use the VNDB Kana API to discover recently released visual novels with
Chinese or English language support. The API is a **REST API** (not GraphQL)
at `POST https://api.vndb.org/kana/vn` with a JSON body.

## Triggers

- Cron job or user asks to check for new Galgame/visual novel releases
- Any task involving VNDB API v2 (Kana) querying

---

## Step 1 — Query VNDB for recent releases

### API endpoint & format

```
POST https://api.vndb.org/kana/vn
Content-Type: application/json
```

The body is a **JSON object**, NOT GraphQL. All fields are optional with defaults:

```json
{
  "filters": [],
  "fields": "",
  "sort": "id",
  "reverse": false,
  "results": 10,
  "page": 1,
  "count": false
}
```

### Essential filters

```json
{
  "filters": [
    "and",
    ["or",
      ["lang", "=", "en"],
      ["lang", "=", "zh-Hans"],
      ["lang", "=", "zh-Hant"],
      ["lang", "=", "zh"]
    ],
    ["released", ">=", "2025-05-01"],
    ["released", "!=", "TBA"]
  ],
  "sort": "released",
  "reverse": true,
  "results": 30
}
```

Key points:
- `"and"` wraps multiple conditions that must ALL match
- `"or"` wraps multiple conditions where ANY match is sufficient
- `["released", "!=", "TBA"]` excludes entries without a concrete release date
- `["id", "=", "v53130"]` filters by single ID — arrays are NOT supported for `id`

### Recommended fields

```json
"fields": "id, title, alttitle, released, image.url, image.sexual, image.violence, description, titles.lang, titles.title, titles.official, developers.name, platforms, length_minutes, rating"
```

- Dot notation selects nested fields: `image.url`, `developers.name`
- Bracket syntax selects multiple: `image{url,sexual,violence}` is equivalent to `image.url, image.sexual, image.violence`
- `image.sexual` is a float (0–3 scale): `> 1.0` is likely NSFW

### Pagination

- `page` is 1-indexed
- Response includes `"more": true` when more pages exist
- Typical page size: 30 results

---

## Step 2 — Parse and curate

### Description cleaning

VNDB descriptions contain BBCode-like markup that must be cleaned for display:

```python
import re
desc = re.sub(r'\[url=[^\]]+\]', '', desc)
desc = desc.replace('[/url]', '')
desc = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', desc)
desc = desc.replace('[', '').replace(']', '')
desc = ' '.join(desc.split())  # normalize whitespace
```

### Curation rules

1. **Prioritize Chinese-supported games** (`zh-Hans` / `zh-Hant` / `zh` in `titles`)
2. **Filter obvious NSFW**: if `image.sexual > 1.0`, consider downgrading or skipping
3. **Prefer games with descriptions** — skip entries without `description`
4. **Look for notable ratings** — `rating > 70` is worth highlighting
5. **Extract Chinese title**: check `zh-Hans` first, then `zh-Hant`, then `zh`
6. **Cover image URL**: VNDB images are at `https://t.vndb.org/cv/{xx}/{xxxxx}.jpg`

---

## Step 3 — Reference sites (supplementary)

The user's reference sites:

| Site | URL | Status |
|------|-----|--------|
| 青桔网 | qingju.net | ❌ Unreachable (connection timeout) |
| Hikarinagi | hikarinagi.com | ⚠️ Nuxt.js SPA — curl returns HTML shell only, browser required |
| NekoGAL | nekogal.com | ❌ Unreachable (connection timeout) |
| TouchGal | touchgal.net | ⚠️ Returns HTTP 403 |

**Hikarinagi** is a Nuxt.js SPA (similar architecture to lightnovel.cn). The SSR state extraction technique documented in `lightnovel-tracker` may apply — check for `window.__NUXT__` in the HTML shell.

For now, VNDB API is the primary and most reliable data source. Reference sites are supplementary and should not block the report if inaccessible.

---

## Output format

Output in **Chinese**. Each game entry:

```
## N. 中文标题（English Title）
- **发售日**：YYYY-MM-DD
- **开发商**：Studio Name
- **平台**：Windows / Linux / ...
- **评分**：⭐ XX.X （if available）
- **语言**：🇨🇳 简体中文 · 🇬🇧 英语 · 🇯🇵 日语

> 中文简介（从 VNDB description 翻译或直接使用中文描述）

![封面](cover_image_url)
```

Include a summary section at the bottom:

```
### 📊 本期小结
- 共计收录 N 款新作
- 其中 X 款支持中文，Y 款英语独占
- 全平台覆盖 ...
```

Target **5–8 games** per report. If there are fewer quality candidates in the window, report what's available rather than padding with irrelevant entries.

---

## Reference files

- `references/vndb-api-reference.md` — Full VNDB Kana API documentation: endpoint, filter syntax, response structure, worked examples, error codes
- `references/chinese-reference-sites.md` — Status of 青桔网, Hikarinagi, NekoGAL, TouchGal and scraping constraints

---

## Pitfalls

- **Not GraphQL**: The Kana API is REST. Sending `{"query": "..."}` or raw GraphQL will return `400 Bad Request`. Send the JSON filter object directly as the body.
- **TBA entries sort first**: When sorting by `released` in reverse, TBA entries appear at the top. Always add `["released", "!=", "TBA"]` to exclude them.
- **ID filter is single-value only**: `["id", "=", ["v1","v2"]]` fails with "Invalid value". Use `["or", ["id","=","v1"], ["id","=","v2"]]` instead.
- **Release dates from far future**: Some entries have dates years in the future — combine `["released", ">=", ...]` with a reasonable upper bound or use a tight window.
- **Reference sites may be down**: Don't let inaccessible reference sites block the report. VNDB is the primary source.
