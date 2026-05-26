# VNDB 新作情报查询（已验证可用）

## 查询：最近发售、含中文/英文的视觉小说

### 第一步：curl 抓取 → 临时文件

```bash
curl -s -X POST "https://api.vndb.org/kana/vn" \
  -H "Content-Type: application/json" \
  -d '{
    "filters": [
      "and",
      ["released", ">=", "2026-05-01"],
      ["or", ["lang", "=", "en"], ["lang", "=", "zh-Hans"], ["lang", "=", "zh-Hant"]],
      ["or", ["olang", "=", "ja"], ["olang", "=", "en"], ["olang", "=", "zh-Hans"], ["olang", "=", "zh-Hant"]]
    ],
    "results": 30,
    "sort": "released",
    "reverse": true,
    "fields": "title,alttitle,titles.title,titles.lang,image.id,released,rating,length,description,developers.name,olang"
  }' -o /tmp/vndb_results.json
```

### 第二步：Python 解析

```python
import json

with open('/tmp/vndb_results.json', 'r') as f:
    data = json.load(f)

results = [r for r in data['results']
           if r.get('released') and r['released'] != 'TBA']

results.sort(key=lambda r: r['released'], reverse=True)

for r in results:
    # 提取多语言标题
    titles = {}
    for t in r.get('titles', []):
        titles[t['lang']] = t['title']

    zh = titles.get('zh-Hans', titles.get('zh-Hant', ''))
    en = titles.get('en', '')
    display = zh or en or r.get('title', '')

    # 封面URL
    img_id = (r.get('image') or {}).get('id', '')
    if img_id:
        num = int(img_id.replace('cv', ''))
        img_url = f"https://t.vndb.org/cv/{num % 256}/{num}.jpg"
    else:
        img_url = ''

    # 简介清理
    desc = (r.get('description') or '暂无简介')
    desc = desc.replace('[b]','').replace('[/b]','').replace('\n',' ')[:300]

    devs = ', '.join([d['name'] for d in r.get('developers', [])]) or '独立制作'

    print(f"{display} | {r['released']} | {r.get('rating','?')} | {devs}")
```

### 第三步：筛选与输出

- 过滤 NSFW：检查 description 含 `sex/porn/hentai/erotic/nsfw` 等关键词
- 优先选有描述、有评分、知名开发商的游戏
- 输出格式：中文标题 + 发售日 + 简介 + 封面图链接
- 每期 5-8 款

## TBA 过滤

VNDB 大量游戏 released 为 "TBA"，必须过滤：
```python
dated = [r for r in results if r.get('released') and r['released'] != 'TBA']
```

## 获取单个 VN 详情

```bash
curl -s -X POST "https://api.vndb.org/kana/vn" \
  -H "Content-Type: application/json" \
  -d '{
    "filters": ["or", ["id","=","v59403"], ["id","=","v64480"]],
    "results": 10,
    "fields": "title,alttitle,titles.title,titles.lang,image.id,released,rating,length,description,developers.name,olang"
  }' -o /tmp/vndb_detail.json
```

## 已知局限

- 新游戏 descriptions 常为 null（VNDB 数据库未收录）
- 缺少描述的可以通过抓取 VNDB 网页版 `vndb.org/v{id}` 获取 tags 辅助撰写简介
- Python `requests` 到 `api.vndb.org` 不可用，必须用 curl
