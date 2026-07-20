# GitHub 禁漫天堂相关工具 (June 2026)

## Python 库

| Repository | Stars | Description |
|-----------|-------|-------------|
| [hect0x7/JMComic-Crawler-Python](https://github.com/hect0x7/JMComic-Crawler-Python) | ★6,445 | Python API 库，支持网页端和移动端，含 GitHub Actions 下载器 |
| [lanyeeee/jmcomic-downloader](https://github.com/lanyeeee/jmcomic-downloader) | ★1,491 | 多线程下载器，带 GUI，支持免费下载收费漫画，已打包 exe |
| [Eix0721/JMcomic-Downloader](https://github.com/Eix0721/JMcomic-Downloader) | ★19 | 命令行交互式漫画下载工具，支持批量下载 |

## APK 安卓客户端

| Repository | Stars | Description |
|-----------|-------|-------------|
| [hect0x7/JMComic-APK](https://github.com/hect0x7/JMComic-APK) | ★5,350 | 官方原版 APK，GitHub Actions 自动构建发布 |
| [Tom6814/JMComic3-APK-NO-Ads](https://github.com/Tom6814/JMComic3-APK-NO-Ads) | ★68 | 去广告版、去游戏版、修复版改版 |
| [niuhuan/jenny](https://github.com/niuhuan/jenny) | ★1,116 | 跨平台漫画浏览器（Flutter），支持 Android/iOS/Mac/Win/Linux |
| [deretame/Breeze](https://github.com/deretame/Breeze) | ★1,622 | Flutter 多源漫画阅读器，支持禁漫/哔咔/ehentai/nhentai 等 |
| [Dedicatus546/jm-mobile](https://github.com/Dedicatus546/jm-mobile) | ★40 | Jetpack Compose 原生 Android 客户端（轻量级） |
| [ComicSparks/jasmine](https://github.com/ComicSparks/jasmine) | ★5,286 | 跨平台漫画浏览器，支持多源插件 |

### 最新 APK 直链

**JMComic-APK v2.0.26（官方原版）**
- 国内加速: `https://ghproxy.net/https://github.com/hect0x7/JMComic-APK/releases/download/2.0.26/2.0.26.apk`
- GitHub: `https://github.com/hect0x7/JMComic-APK/releases/download/2.0.26/2.0.26.apk`
- SHA256: `d8b2d01c70cea0b8953814a8322884c7c21ceb282c26cd32aabfc0dfa7b3db74`

**JMComic3-APK-NO-Ads v2.0.21（去广告版）**
- `https://github.com/Tom6814/JMComic3-APK-NO-Ads/releases/download/v2.0.21-noupdate-fix/jmcomic3_v2.0.21_noupdate_fix.apk`

## 其他多源应用

| Repository | Stars | Description |
|-----------|-------|-------------|
| [wgh136/PicaComic](https://github.com/wgh136/PicaComic) | ★8,649 | Flutter 漫画应用，支持多源 |
| [tonquer/JMComic-qt](https://github.com/tonquer/JMComic-qt) | ★3,881 | PC 客户端（Qt），支持 Win/Linux/Mac |
| [delta-comic/delta-comic](https://github.com/delta-comic/delta-comic) | ★164 | Tauri/Android 多源漫画聚合客户端 |

## 下载加速方法

国内服务器下载 GitHub Release assets 时，推荐以下方式：

### 1. ghproxy.net（推荐）
```bash
# 通过国内 CDN 镜像加速
curl -L "https://ghproxy.net/https://github.com/{owner}/{repo}/releases/download/{tag}/{file}" -o output
```

### 2. aria2c 多线程（推荐大文件）
```bash
aria2c -x 8 -s 8 -k 1M \
  --continue=true -d /tmp -o output.apk \
  "https://ghproxy.net/https://github.com/{owner}/{repo}/releases/download/{tag}/{file}"
```

### 3. 获取 CDN 直链后下载
```bash
# 步骤1：通过代理获取重定向到 Azure CDN 的 URL
proxy="http://127.0.0.1:7897"
cdn_url=$(curl -sI -x "$proxy" "https://github.com/{owner}/{repo}/releases/download/{tag}/{file}" \
  -H "User-Agent: Mozilla/5.0" 2>&1 | grep -i "^location:" | sed 's/^[Ll]ocation: //')

# 步骤2：直接用 CDN 链接下载（注意 URL 有特殊字符要用 --url 转义）
curl -L --url "$cdn_url" -o output
```

## Search Notes

GitHub API 搜索禁漫天堂相关工具时注意：
- 使用匿名 API（不要 Bearer token）有时反而能搜到结果（如果 token 没有 search scope）
- 搜索词: `18comic`, `jmcomic`, `禁漫天堂`, `18comic downloader`, `jmcomic android`
- GitHub 匿名 API 速率限制: 10 req/min
- Fine-grained token (`github_pat_*`) 默认没有 search scope，需要用 classic token (`ghp_*`)
- 如果 API 返回 total_count=0 且没有错误消息，大概率是 token 的 search scope 权限不足
