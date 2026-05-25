# Chinese-Accessible Research Sites

Reference sites that work reliably from this user's WSL/China environment.
When web searches time out on international search engines, use these instead.

## Encyclopedia / Background Research

| Site | URL | Best For |
|------|-----|----------|
| 百度百科 | https://baike.baidu.com | Anime, novels, film, general reference. Fast, rarely times out. |
| 中文维基百科 | https://zh.wikipedia.org | More neutral/authoritative. Slower from China; try Baidu Baike first. |

## Anime / Bangumi Info

| Site | URL | Best For |
|------|-----|----------|
| 番组计划 | https://bangumi.tv | Anime ratings, summaries, staff/cast details |
| 哔哩哔哩 | https://www.bilibili.com | Streaming info, user reviews, episode guides |

## Light Novels

| Site | URL | Best For |
|------|-----|----------|
| 轻之国度 | https://www.lightnovel.cn | Latest updates, rankings, news, translation discussions |
| 轻小说文库 | https://www.wenku8.net | Novel listings, hot lists, tags |

## News / Official Sources

| Site | URL | Best For |
|------|-----|----------|
| 新华网 | https://www.news.cn | Official news, clean structure, rarely blocked |
| 人民网 | https://www.people.com.cn | Same as above |
| 央视网 | https://tv.cctv.com | Anime/film official announcements |

## Search Engines (from China)

| Site | URL | Notes |
|------|-----|-------|
| 百度 | https://www.baidu.com/s?wd=关键词 | Preferred search engine. Works. |
| 必应国内版 | https://cn.bing.com/search?q=关键词 | Fallback if Baidu rate-limits |

## Scraping Technique

### curl + python3 pipeline (tested working):
```bash
# 1. Fetch page
curl -sL "https://baike.baidu.com/item/永远的黄昏" \
  -H "User-Agent: Mozilla/5.0" \
  -o /tmp/page.html

# 2. Extract text
python3 -c "
import re
with open('/tmp/page.html') as f:
    content = f.read()
text = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.DOTALL)
text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
text = re.sub(r'<[^>]+>', ' ', text)
text = re.sub(r'\s+', ' ', text)
# Search for keywords
for keyword in ['主题曲', '配音', '导演']:
    idx = text.find(keyword)
    if idx > 0:
        print(text[max(0,idx-50):idx+300])
        print()
"
```

### Key tips:
- ALWAYS set `User-Agent: Mozilla/5.0` header
- Use `-o` to save to disk, then process with Python (avoid pipe encoding issues)
- Strip HTML tags first, then search for Chinese keywords
- `re.DOTALL` flag is essential for multi-line content
- 百度百科 URLs: `https://baike.baidu.com/item/URL_ENCODED_TITLE`

## Sites Known to Fail from China

These consistently timeout or fail from this environment — **do not bother retrying**:
- Google, Bing (international), DuckDuckGo
- catbox.moe, 0x0.st, gofile.io, s-ul.eu, upload.ee (file hosting)
- wsrv.nl (image proxy)
- GitHub raw, GitHub pages (sometimes works, usually slow)
- t.vndb.org (VNDB images) — works eventually but 10-25s per image

## Chinese AI API Providers (Free Tiers)

When building API relay stations or adding model backends, these Chinese providers offer free tiers:

| Provider | Model | Base URL | Free Quota | Registration |
|----------|-------|----------|------------|--------------|
| 通义千问 (Qwen) | qwen-turbo | https://dashscope.aliyuncs.com/compatible-mode/v1 | 100万T/月 | bailian.console.aliyun.com |
| 通义千问 (Qwen) | qwen-plus | same base | 100万T/月 | same |
| 豆包 (Doubao) | doubao-lite-128k | https://ark.cn-beijing.volces.com/api/v3 | 50万T/天 | console.volcengine.com/ark |
| 豆包 (Doubao) | doubao-pro-128k | same base | 50万T/天 | same |
| 智谱 (GLM) | glm-4-flash | https://open.bigmodel.cn/api/paas/v4 | 注册即送 | open.bigmodel.cn |
| 硅基流动 | deepseek-ai/DeepSeek-V3 | https://api.siliconflow.cn/v1 | varies | siliconflow.cn |

All use OpenAI-compatible API format (`/chat/completions`, `Authorization: Bearer KEY`).
API keys go in `~/.hermes/.env`:
```bash
DASHSCOPE_API_KEY=sk-xxx    # 通义千问
DOUBAO_API_KEY=sk-xxx        # 豆包
ZHIPU_API_KEY=sk-xxx         # 智谱
SILICONFLOW_API_KEY=sk-xxx   # 硅基流动
```
