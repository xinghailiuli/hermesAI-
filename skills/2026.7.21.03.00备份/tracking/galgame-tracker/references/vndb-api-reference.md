# VNDB Kana API — Query Format Reference

## Endpoint

```
POST https://api.vndb.org/kana/vn
Content-Type: application/json
```

Other endpoints: `/kana/release`, `/kana/producer`, `/kana/character`, `/kana/staff`, `/kana/tag`, `/kana/trait`

## Request Body Structure

```json
{
  "filters": [],
  "fields": "",
  "sort": "id",
  "reverse": false,
  "results": 10,
  "page": 1,
  "user": null,
  "count": false,
  "compact_filters": false,
  "normalized_filters": false
}
```

All members are optional.

## Filter Operators

| Operator | Meaning |
|----------|---------|
| `=` | Equal |
| `!=` | Not equal |
| `>` | Greater than |
| `>=` | Greater than or equal |
| `<` | Less than |
| `<=` | Less than or equal |

## Compound Filters

```json
["and", filter1, filter2, ...]   // ALL must match
["or", filter1, filter2, ...]    // ANY must match
```

## VN Filters (commonly used)

| Filter | Type | Description |
|--------|------|-------------|
| `id` | string | VN ID (e.g. "v17") |
| `lang` | string | Language code: "en", "ja", "zh-Hans", "zh-Hant", "zh", "ru", "ko", etc. |
| `released` | string | Release date "YYYY-MM-DD" or "TBA" |
| `platform` | string | Platform: "win", "lin", "mac", "and", "ios", "web", "swi", etc. |
| `length` | int | Length in minutes |
| `developer` | string | Developer ID |
| `tag` | string | Tag ID |

The `lang` filter has the **'m' flag** (multi-match): a VN with both English and Japanese matches both `["lang","=","en"]` and `["lang","=","ja"]`.

## Response Structure

```json
{
  "results": [...],
  "more": true,
  "count": 1234
}
```

- `results`: array of VN objects with requested fields
- `more`: boolean, true if more pages available
- `count`: total matching entries (only when `"count": true`)

## Image Object

```json
{
  "url": "https://t.vndb.org/cv/20/95420.jpg",
  "sexual": 0.0,
  "violence": 0.0,
  "dims": [400, 600]
}
```

- `sexual`: float 0–3 (VNDB sexual content rating)
- `violence`: float 0–3 (VNDB violence rating)
- `url`: relative to `https://t.vndb.org/`

## Titles Array

```json
[
  {"lang": "en", "title": "Iris Odyssey", "official": true},
  {"lang": "zh-Hans", "title": "爱里斯 奥德赛", "official": true},
  {"lang": "zh-Hant", "title": "愛里斯 奧德賽", "official": true},
  {"lang": "ja", "title": "アイリス・オデッセイ", "official": true}
]
```

- `lang`: ISO 639-1 or BCP 47 language tag
- `official`: whether the title is official (vs. romanization/fan translation)

## Worked Query Examples

### Recent Chinese/English VNs (main query)

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
    ["released", ">=", "2025-05-15"],
    ["released", "!=", "TBA"]
  ],
  "fields": "id, title, alttitle, released, image.url, image.sexual, image.violence, description, titles.lang, titles.title, titles.official, developers.name, platforms, length_minutes, rating",
  "sort": "released",
  "reverse": true,
  "results": 30
}
```

### Fetch specific VNs by ID

```json
{
  "filters": ["or", ["id","=","v53130"], ["id","=","v58103"], ["id","=","v64728"]],
  "fields": "id, title, released, image.url, description, titles.lang, titles.title",
  "results": 20
}
```

### Look up VN by title (use release endpoint for better results)

For title search, use the `/kana/release` endpoint with `vn` field or the main VNDB search:
```
https://vndb.org/v/all?q=search+terms&fil=lang-en.lang-zh
```

## Error Responses

| HTTP Code | Body | Cause |
|-----------|------|-------|
| 400 | `Invalid request (most likely: invalid JSON or non-UTF8 data).` | Body is not valid JSON |
| 400 | `Unknown member 'query'.` | Sent GraphQL wrapper `{"query": "..."}` |
| 400 | `Invalid 'id' filter: Invalid value.` | ID filter with array value, use `or` instead |
