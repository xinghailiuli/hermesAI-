#!/usr/bin/env python3
"""日轻新作情报 - 轻之国度 scraper
抓取 https://www.lightnovel.cn 轻小说 > 最新 板块
输出 JSON 供 cron agent 播报

关键发现：
- URL: /category/3/106?type=1 (最新), /category/3/107?type=1 (整卷)
- 链接格式: href="/cn/detail/ID" (注意 /cn/ 前缀)
- 标题在: <a title="[作者]书名[元数据]">.class="module-title" 属性中的 title
- 时间在: <div class="create-time">
- 需要过滤 pinned 帖: 含 "置顶" "版规" "勋章" "工资" 的跳过
- 国内直接 curl 可达，无需 headless/JS
"""
import json, re, sys, urllib.request, ssl

ssl_ctx = ssl.create_default_context()
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

def fetch(url, timeout=15):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "zh-CN,zh;q=0.9",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl_ctx) as r:
            return r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"[WARN] fetch failed: {url} - {e}", file=sys.stderr)
        return ""

def parse_title(title):
    """Parse [author] title [metadata]"""
    title = title.strip()
    author = ""
    m = re.match(r'^\[([^\]]+)\]\s*(.+)', title)
    if m:
        author = m.group(1)
        rest = m.group(2)
    else:
        rest = title
    meta = ""
    meta_m = re.findall(r'\[([^\]]+)\]$', rest)
    if meta_m:
        meta = meta_m[-1]
        rest = re.sub(r'\s*\[[^\]]+\]$', '', rest)
    return {"author": author, "title": rest, "meta": meta}

def scrape_lightnovel_cn():
    """轻之国度 轻小说最新"""
    url = "https://www.lightnovel.cn/category/3/106?type=1"
    html = fetch(url)
    if not html:
        return []

    # Pattern: <a href="/cn/detail/ID" title="[author] TITLE [meta]" class="module-title">
    #   ... <div class="create-time">TIME</div>
    items = re.findall(
        r'<a\s+href="(/cn/detail/\d+)"[^>]*title="([^"]+)"[^>]*class="module-title[^"]*"[^>]*>.*?</a>.*?create-time[^>]*>([^<]+)',
        html, re.DOTALL
    )

    seen = set()
    results = []
    for href, raw_title, time_str in items:
        t = raw_title.strip()
        if not t or len(t) < 3 or t in seen:
            continue
        if any(kw in t for kw in ['置顶', '版规', '勋章', '工资']):
            continue
        seen.add(t)

        parsed = parse_title(t)
        results.append({
            "title": parsed["title"],
            "author": parsed["author"],
            "meta": parsed["meta"],
            "time": time_str.strip(),
            "url": f"https://www.lightnovel.cn{href}",
            "site": "轻之国度",
        })

    return results[:15]

def main():
    data = {"lightnovel_cn": scrape_lightnovel_cn()}
    print(json.dumps(data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
