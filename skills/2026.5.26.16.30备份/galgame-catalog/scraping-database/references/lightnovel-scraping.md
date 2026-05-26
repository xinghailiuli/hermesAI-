# 轻小说情报采集 — 轻之国度 (lightnovel.cn)

## 适用场景

采集日轻/韩轻翻译更新情报，用于 cron 自动播报。用户只读日轻韩轻翻译，不读国产网文。

## 数据源

| 站点 | URL | 状态 |
|------|-----|------|
| 轻之国度（主力） | `https://www.lightnovel.cn/category/3/106?type=1` | ✅ 可用 |
| 哔哩轻小说 | `https://www.bilinovel.com/` | ❌ Cloudflare 盾 |
| 轻小说文库 | `https://www.wenku8.net/` | ⚠️ 302 重定向 |

## 轻之国度 HTML 结构

### 页面

`/category/3/106?type=1` — 「輕小說」→「最新」

### 条目结构

```html
<a href="/cn/detail/1144366" target="_blank" 
   title="[西条阳]不过是偶像！～但是果然颜值好高～[⚡️文库]" 
   class="module-title text-hide-3">
  <span class="title">[西条阳]不过是偶像！～但是果然颜值好高～[⚡️文库]</span>
</a>
...
<div class="create-time">2 小时前</div>
```

### 提取规则

```python
# 正则：匹配 /cn/detail/ID href，提取 title 属性和时间
pattern = r'<a\s+href="(/cn/detail/\d+)"[^>]*title="([^"]+)"[^>]*class="module-title[^"]*"[^>]*>.*?</a>.*?create-time[^>]*>([^<]+)'

# 标题解析：[作者名] 作品名 [元数据/文库]
import re
m = re.match(r'^\[([^\]]+)\]\s*(.+)', title)  # author = m.group(1), rest = m.group(2)
meta = re.findall(r'\[([^\]]+)\]$', rest)      # trailing metadata
```

### 需要过滤的条目

跳过以下关键词（版务帖）：
- `置顶`
- `版规`
- `勋章`
- `工资`

### 注意事项

- 页面是 Nuxt/Vue SSR，HTML 中包含完整数据，不需要 JS 渲染
- 无需 Cookie/登录即可访问
- URL 是 `/cn/detail/ID`（注意 `/cn/` 前缀）
- 时间格式：`X 小时前`、`X 天前`、`X 分钟前`

### 分页陷阱

`?page=N` 参数**可能返回重复条目**（同一条目出现在多页），必须按 `/cn/detail/ID` 去重。实际可用条目约 15 条/3天，不要依赖页码控制总量。

### 详情页简介提取

详情页是 Nuxt SSR，简介嵌入在 `__NUXT__` JavaScript 全局变量中，不是 HTML 标签：

```python
# 从 Nuxt state 提取 summary
m = re.search(r'article:\{[^}]*?summary:"([^"]+)"', html)
if m:
    summary = m.group(1)
    # 解码 Unicode 转义
    summary = summary.replace('\\u002F', '/').replace('\\u003C', '<').replace('\\u003E', '>').replace('\\"', '"')
```

`summary` 字段通常是正文第一段，约 150-300 字符，适合作为播报简介。

### 日轻/韩轻 vs 国产网文过滤

轻之国度 `gid=106`（輕小說）板块已天然过滤大部分国产网文，但仍需二次过滤：

```python
def is_likely_jp_kr(author, meta):
    """通过作者名和元数据判断是否为日轻/韩轻"""
    # 日本文库标记
    jp_markers = ['台/繁', '台/简', '文库', 'MF', 'GCN', 'HJ', '电击', '角川',
                  '富士见', 'GA', '一迅社', '讲谈社', '集英社', '小学馆', 'OVERLAP',
                  'Sneaker', 'Fami通', 'DASH', 'ノベル', '⚡']
    for m in jp_markers:
        if m in meta: return True
    # 韩文作者
    if re.search(r'[\uAC00-\uD7AF]', author): return True
    # 日文假名
    if re.search(r'[\u3040-\u309F\u30A0-\u30FF]', author): return True
    # 日式汉字名（2-6字纯汉字）
    if re.match(r'^[\u4e00-\u9fff]{2,6}$', author): return True
    # 无作者且无日文特征 → 跳过
    if not author: return False
    return True
```

### 时间解析与3日过滤

```python
from datetime import datetime, timedelta

def parse_time_ago(time_str):
    now = datetime.now()
    m = re.match(r'(\d+)\s*小时前', time_str)
    if m: return now - timedelta(hours=int(m.group(1)))
    m = re.match(r'(\d+)\s*天前', time_str)
    if m: return now - timedelta(days=int(m.group(1)))
    m = re.match(r'(\d+)\s*分钟前', time_str)
    if m: return now - timedelta(minutes=int(m.group(1)))
    return None

# 过滤3天内
cutoff = datetime.now() - timedelta(days=3)
items = [i for i in items if i['parsed_dt'] and i['parsed_dt'] >= cutoff]
```

## 脚本位置

`~/.hermes/scripts/lightnovel_scraper.py`

## Cron 配置

- Job: `e1a1237f4e76`「每日轻小说新作情报」
- 时间：每天 09:30
- 模式：`no_agent=false`，agent 从脚本输出的 JSON 精选 5-8 本播报
