# Chinese Video Platforms — Cloud Server Accessibility

On Chinese cloud servers (Alibaba Cloud ECS, Tencent Cloud, etc.), domestic video platforms are directly accessible **without any proxy**. yt-dlp works well for most.

## Quick Test Results (Alibaba Cloud Hangzhou ECS)

| Platform | URL | HTTP Status | Latency | yt-dlp Support |
|----------|-----|:-----------:|---------|:--------------:|
| 哔哩哔哩 (Bilibili) | bilibili.com | 200 | 0.1s | ✅ Excellent |
| 抖音 (Douyin) | douyin.com | 200 | 0.15s | 🟡 Limited |
| 西瓜视频 (iXigua) | ixigua.com | 200 | 0.24s | ✅ Good |
| 腾讯视频 (Tencent Video) | v.qq.com | 200 | 0.3s | 🟡 Limited |
| 优酷 (Youku) | youku.com | 200 | 0.18s | 🟡 Limited |

## yt-dlp Quick Usage

```bash
# Bilibili — best support, handles BV/av numbers
yt-dlp "https://www.bilibili.com/video/BVxxxxxx" -o "~/Downloads/%(title)s.%(ext)s"

# With cookies for HD/会员 content
yt-dlp --cookies-from-browser chrome "https://www.bilibili.com/video/BVxxxxxx"

# Best quality merge
yt-dlp -f "bestvideo+bestaudio" --merge-output-format mp4 "URL"
```

## Foreign Sites — Blocked (Same Server)

| Platform | Proxy | Direct | Cause |
|----------|:-----:|:------:|-------|
| YouTube | ❌ | ❌ | Cloud DPI + GFW |
| Twitter/X | ❌ | ❌ | Cloud DPI + GFW |
| iwara.tv | ❌ | ❌ | Cloud DPI + GFW |
| GitHub | ✅ | ❌ | CDN allows dev sites |

## See Also

- `cloud-proxy-setup` skill — proxy setup and airport filtering diagnostics
- `cloud-proxy-setup` pitfalls — cloud DPI and protocol upgrade recommendations
