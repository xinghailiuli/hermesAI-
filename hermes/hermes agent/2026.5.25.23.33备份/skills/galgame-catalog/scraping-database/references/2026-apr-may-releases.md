# 2026年4-5月 Galgame 新作速查

> 最后更新：2026-05-22
> 数据来源：VNDB API（已验证）+ 必应搜索（Chromium headless）+ CnGal

## VNDB API 查询命令

### 4-5月日系新作（含评分）
```bash
curl -s -X POST "https://api.vndb.org/kana/vn" \
  -H "Content-Type: application/json" \
  -d '{"filters":["and",["released",">=","2026-04-01"],["released","<=","2026-05-31"],["lang","=","ja"]],"results":50,"fields":"title,alttitle,released,developers.name,rating","sort":"released","reverse":false}' \
  | python3 -c "
import json, sys
data = json.load(sys.stdin)
for vn in data.get('results', []):
    title = vn.get('title','?')
    alt = vn.get('alttitle','')
    rel = vn.get('released','')
    rating = vn.get('rating',0) or 0
    print(f\"【{rel}】{title}{' / '+alt if alt else ''} ⭐{rating:.1f}\")
"
```

### 5月限定（所有语言）
```bash
curl -s -X POST "https://api.vndb.org/kana/vn" \
  -H "Content-Type: application/json" \
  -d '{"filters":["and",["released",">=","2026-05-01"],["released","<=","2026-05-31"]],"results":30,"fields":"title,alttitle,released,rating","sort":"released","reverse":false}'
```

## 2026年4月 日系主要新作

| 日期 | 游戏 | 评分 |
|------|------|------|
| 4/24 | にょにんじま2 | ⭐7.5 |
| 4/23 | マツリカの炯-kEi- 天命華燭伝 | ⭐7.4 |
| 4/15 | Bunny Garden 2 / バニーガーデン2 | ⭐7.2 |
| 4/10 | 私、彼氏がいるのに……っ！ | ⭐5.7 |
| 4/09 | Memories Off 双想 Break out of my shell | — |
| 4/09 | 名探偵カヌレの事件ダイアリー | — |
| 4/14 | 四月某日、花降る夜 | — |
| 4/17 | 淀み海の溺れ唄 | — |

## 中文源补充确认

| 源 | 方法 | 结果 |
|----|------|------|
| VNDB API | curl POST | ✅ 30+条/月 |
| 必应搜索 | Chromium headless | ✅ 可用 |
| CnGal | Chromium headless | ✅ 可用（发现"异乡情缘Demo"更新） |
| B站 | Chromium headless | ❌ 需登录 |
| 贴吧 | Chromium headless | ❌ 需登录 |
| 2DFan | 任何方法 | ❌ Cloudflare 盾 |
| TouchGal | Chromium headless | ⚠️ 不稳定 |
| Bangumi | Chromium headless | ❌ 需登录 |

## 实战注意事项

- VNDB 过滤器 `["released",">","2026-04-01"]` 用 `>` 会返回大量 TBA（待定）结果；用 `["and", [">=","date1"], ["<=","date2"]]` 精确限定范围
- VNDB 的 `["lang","=","ja"]` 过滤器不够精确，需要 Python 二次用假名范围 `0x3040-0x30ff` 筛掉英文标题的日文标签游戏
- 多数"日系"在 VNDB 的 `lang` 字段为 `ja`，但欧美独立作也可能有日文标签
- 必应搜索关键词避免用"2026年"等通配词（会被日历、新闻淹没），用具体的"galgame 新作 发售 5月"
