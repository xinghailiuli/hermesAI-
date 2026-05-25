# AniList GraphQL API 探索参考

> 用于发现动漫、漫画、音乐等二次元内容的 API，无需认证、直接 POST JSON。

## 基础用法

```bash
curl -s -X POST "https://graphql.anilist.co" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -H "User-Agent: Mozilla/5.0" \
  -d '{"query":"{Page(page:1,perPage:5){media(type:ANIME,sort:POPULARITY_DESC){title{native romaji}averageScore genres}}}"}'
```

**注意**：Python `urllib.request` 会被 AniList 403 拒绝，必须用 `curl`（curl 的 User-Agent 和 header 组合能通过）。

## 常用查询模板

### 正在放送的热门动画
```graphql
{
  Page(page: 1, perPage: 8) {
    media(type: ANIME, status: RELEASING, sort: POPULARITY_DESC) {
      title { native romaji }
      genres
      averageScore
      siteUrl
      episodes
    }
  }
}
```

### 既定年份高分动画
```graphql
{
  Page(page: 1, perPage: 6) {
    media(type: ANIME, seasonYear: 2025, sort: SCORE_DESC) {
      title { native romaji }
      averageScore
      genres
      format
      siteUrl
    }
  }
}
```

### 冷门高分（限制 popularity 上限）
```graphql
{
  Page(page: 1, perPage: 6) {
    media(type: ANIME, status: FINISHED, sort: SCORE_DESC, popularity_lesser: 50000) {
      title { native romaji }
      averageScore
      genres
      popularity
      seasonYear
    }
  }
}
```

### 特定类型（音乐、运动、治愈系）
```graphql
# 音乐题材
{ Page(page:1,perPage:6){media(type:ANIME,genre:"Music",sort:SCORE_DESC){title{native romaji}averageScore seasonYear}} }

# 运动题材
{ Page(page:1,perPage:5){media(genre:"Sports",type:ANIME,status:RELEASING,sort:SCORE_DESC){title{native romaji}averageScore genres}} }

# 日常/治愈
{ Page(page:1,perPage:5){media(type:ANIME,genre:"Slice of Life",sort:SCORE_DESC,status:FINISHED){title{native romaji}averageScore seasonYear}} }
```

### Galgame/视觉小说改编
```graphql
{
  Page(page: 1, perPage: 6) {
    media(type: ANIME, source: VISUAL_NOVEL, sort: SCORE_DESC) {
      title { native romaji }
      averageScore
      seasonYear
    }
  }
}
```

### 即将上映的漫改
```graphql
{
  Page(page: 1, perPage: 5) {
    media(type: ANIME, source: MANGA, status: NOT_YET_RELEASED, sort: POPULARITY_DESC) {
      title { native romaji }
      genres
      siteUrl
    }
  }
}
```

### 连载中热门漫画
```graphql
{
  Page(page: 1, perPage: 8) {
    media(type: MANGA, status: RELEASING, sort: POPULARITY_DESC, countryOfOrigin: JP) {
      title { native romaji }
      genres
      averageScore
      siteUrl
      chapters
    }
  }
}
```

## 关键字段说明

| 字段 | 说明 |
|------|------|
| `type` | ANIME / MANGA |
| `sort` | POPULARITY_DESC / SCORE_DESC / TRENDING_DESC |
| `status` | RELEASING / FINISHED / NOT_YET_RELEASED |
| `source` | MANGA / VISUAL_NOVEL / LIGHT_NOVEL / ORIGINAL |
| `popularity_lesser` | 限制受众数上限（挖冷门用） |
| `countryOfOrigin` | JP (日本) / KR (韩国) / CN (中国) |

## 实际使用模式：管道到 python3 格式化

```bash
curl -s ... | python3 -c "
import json, sys
d = json.load(sys.stdin)
for m in d['data']['Page']['media']:
    t = m['title']['native'] or m['title']['romaji']
    s = m.get('averageScore', '?')
    print(f'{t} | ⭐{s}%')
"
```

## 注意事项

- ⚠️ Python `urllib.request` 直接调会 403，用 `curl` 🐚
- 速率限制：无官方限制，但建议请求间留间隔
- 标题 `native` 字段为日文原名，`romaji` 为罗马音
- `popularity_lesser` 值越大越热门，值越小越冷门（50000 = 中等偏冷门）
