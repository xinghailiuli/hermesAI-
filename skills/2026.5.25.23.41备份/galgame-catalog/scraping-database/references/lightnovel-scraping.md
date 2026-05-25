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
- 时间格式：`X 小时前`、`X 天前`

## 脚本位置

`~/.hermes/scripts/lightnovel_scraper.py`

## Cron 配置

- Job: `e1a1237f4e76`「每日轻小说新作情报」
- 时间：每天 09:30
- 模式：`no_agent=false`，agent 从脚本输出的 JSON 精选 5-8 本播报
