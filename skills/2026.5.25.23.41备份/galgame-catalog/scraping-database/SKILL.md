---
name: scraping-database
description: Galgame年鉴爬虫与数据库。用curl/requests抓取参考站数据，sqlite3本地存储游戏信息。
---

# 爬虫 & 数据库

## 可用工具

| 工具 | 用途 |
|------|------|
| `curl` | 快速试探网页，终端直接调用 |
| `requests` | Python HTTP请求，带header/cookie |
| `re` | 正则提取数据 |
| `html.parser` | Python内置HTML解析（备用） |
| `sqlite3` | 本地单文件数据库 |
| `json` | VNDB API返回JSON处理 |

BeautifulSoup/lxml 需安装：`pip install beautifulsoup4 lxml --break-system-packages`

## 一、快速爬取（curl → 终端）

### 1.1 直接抓页面
```bash
curl -sL -H "User-Agent: Mozilla/5.0" "https://目标站/页面" | head -200
```

### 1.2 抓取后正则提取
```bash
# 提取所有图片链接
curl -sL "URL" | grep -oP 'src="\K[^"]+\.(jpg|png|webp)'
# 提取标题
curl -sL "URL" | grep -oP '<title>\K[^<]+'
```

## 二、Python爬虫（requests + re）

### 2.1 基础模板
```python
import requests, re, sqlite3, json, time

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def fetch(url):
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.encoding = 'utf-8'
    return resp.text

html = fetch("https://example.com")
# 正则提取
titles = re.findall(r'<h2[^>]*>(.*?)</h2>', html, re.S)
```

### 2.2 VNDB API（获取游戏元数据）
```python
def vndb_search(title):
    """POST到 api.vndb.org/kana/vn 搜索游戏"""
    resp = requests.post(
        "https://api.vndb.org/kana/vn",
        headers={"Content-Type": "application/json"},
        json={
            "filters": ["search", "=", "title", title],
            "results": 5,
            "fields": "title,alttitle,image.url,released,rating,length,developers.name"
        }
    )
    return resp.json()["results"]

# 注意：image.url 里的ID ≠ VN ID，需要单独请求获取原图
# 封面图URL格式：https://t.vndb.org/{image_id} （缩略图）
# 原图：https://t.vndb.org/{image_id}?{vn_id}
```

### 2.3 正则常用模式
```python
# 提取图片 src
re.findall(r'src="([^"]+)"', html)
# 提取链接 href
re.findall(r'href="([^"]+)"', html)
# 提取标签内容
re.findall(r'<div class="title">(.*?)</div>', html, re.S)
# 提取中文（过滤日文）
re.findall(r'[\u4e00-\u9fff]+', text)
```

## 三、sqlite3 数据库

### 3.1 创建 & 建表
```python
import sqlite3
conn = sqlite3.connect("/mnt/c/Users/Administrator/Desktop/galgame_assets/galgame.db")
c = conn.cursor()

c.execute('''
    CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title_cn TEXT,       -- 中文译名
        title_jp TEXT,       -- 日文原名
        vndb_id TEXT UNIQUE, -- VNDB ID
        cover_url TEXT,      -- 封面图URL
        cover_local TEXT,    -- 本地封面路径
        released TEXT,       -- 发售日期
        rating REAL,         -- 评分
        developer TEXT,      -- 开发商
        description TEXT,    -- 简介
        tags TEXT,           -- JSON数组标签
        music_url TEXT,      -- 音乐链接
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()
```

### 3.2 增删改查
```python
# 插入（防重复）
c.execute("INSERT OR IGNORE INTO games (title_cn, vndb_id, cover_url) VALUES (?,?,?)",
          ("Summer Pockets", "v12345", "https://..."))

# 查询
c.execute("SELECT * FROM games WHERE title_cn LIKE ?", ("%Summer%",))
rows = c.fetchall()

# 更新
c.execute("UPDATE games SET cover_local=? WHERE vndb_id=?", ("covers/sp.jpg", "v12345"))

# 导出JSON
c.execute("SELECT * FROM games")
games = [dict(zip([d[0] for d in c.description], row)) for row in c.fetchall()]
with open("games.json", "w", encoding="utf-8") as f:
    json.dump(games, f, ensure_ascii=False, indent=2)

conn.commit()
conn.close()
```

## 四、参考站爬取策略

### 青桔网 (qingju.net 或类似)
- 列表页：curl 抓取游戏列表 → 正则提取标题+链接+封面

### Hikarinagi / NekoGAL
- 用 requests 模拟浏览器访问
- 注意可能需要 cookie 或 referer

### 2DFan
- 可能需要处理反爬（Cloudflare等）
- 降级方案：手动复制数据

### 通用策略
1. 先用 curl 快速试探，看返回的是动态还是静态页面
2. 静态页面 → requests + re 直接提取
3. 动态页面（SPA）→ 找API接口（F12 Network查看）
4. 图片下载后检查大小，<1KB 基本是占位图/失败

## 五、图片批量下载

```python
import os
def download_cover(url, save_path):
    resp = requests.get(url, headers=HEADERS, timeout=30)
    if len(resp.content) < 500:
        print(f"⚠️ 图片过小({len(resp.content)}B)，可能失败: {url}")
        return False
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "wb") as f:
        f.write(resp.content)
    return True
```

## 注意事项
- 频率控制：请求之间 `time.sleep(1-3)` 避免被封
- User-Agent 必须伪装成浏览器
- 图片146B = VNDB默认占位图，需跳过
- VNDB image ID ≠ VN ID，需通过API获取正确封面ID
- 数据库文件放在 `galgame_assets/` 下统一管理

## 中国网络环境下可用源

当 Google / DuckDuckGo 超时不可用时，参考 `references/china-accessible-search.md`。该文件列出了百度百科、Bangumi、哔哩哔哩、百度搜索等中文网站的 curl 爬取模式。
