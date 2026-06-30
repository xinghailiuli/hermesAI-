---
name: chinese-comic-retrieval
category: tools
description: 在中文漫画/本子平台（禁漫天堂/jmcomic/18comic 等）上检索作品信息。涵盖圈内黑话解读、API 调用、网络限制绕过等。
---

# 中文漫画/本子资源检索

本技能涵盖在中文二次元漫画/本子平台上根据用户提供的编号或关键词检索作品。

## 圈内术语

- **车牌号/车号** — 在本子圈/禁漫天堂语境下，指**漫画作品编号（ID）**。用户说"车牌号"时，是在问特定编号对应的作品。
- **禁漫天堂** — 即 jmcomic/18comic，国内最大的中文本子站点

## 平台信息

### 禁漫天堂 (jmcomic / 18comic)

- **Python 库**: `jmcomic` (GitHub: hect0x7/JMComic-Crawler-Python)
- **安装**: `pip install jmcomic` (需要 `--break-system-packages` 在系统 Python 环境下)
- **API 域名池**（动态更新，需从 setting 接口获取）:
  - `www.cdnhjk.net` (Cloudflare) — 国内直连可能超时
  - `www.cdngwc.cc` (Cloudflare)
  - `www.cdngwc.net` (Cloudflare)
  - `www.cdngwc.club` (Cloudflare)
  - `www.cdnutc.me` (非 Cloudflare) — **国内可直连**

### 网络限制

- 18comic.vip / 18comic.org 等主域名在国内被 SNI 阻断，无法直连
- Cloudflare 保护的 CDN 域名（带 .club/.net/.cc 后缀）通过代理时有 TLS 握手问题
- **`www.cdnutc.me` 直连可通**（不通过代理），适合 API 调用
- 搜索 API 返回加密数据（AES 加密），需通过 `JmApiResp.model_data` 解密

## API 调用方式

### 手动调用（不依赖 jmcomic 库）

禁漫天堂 API 需要认证头（token + tokenparam，基于时间戳生成）：

```python
import requests
from jmcomic import JmCryptoTool, time_stamp

ts = time_stamp()
token, tokenparam = JmCryptoTool.token_and_tokenparam(ts)

headers = {
    "Accept-Encoding": "gzip, deflate",
    "User-Agent": "Mozilla/5.0 (Linux; Android 9; V1938CT Build/PQ3A.190705.11211812; wv) AppleWebKit/537.36",
    "token": token,
    "tokenparam": tokenparam,
}

# 查漫画详情 — ID 不存在时返回 {"code":200,"data":[]}
resp = requests.get(f"https://www.cdnutc.me/album/{album_id}", headers=headers, timeout=10)

# 搜索 — 返回加密数据，需用 JmApiResp 解密
resp = requests.get(
    f"https://www.cdnutc.me/search?search_query={keyword}&main_tag=0&page=1",
    headers=headers,
    timeout=10
)
from jmcomic import JmApiResp
jmresp = JmApiResp(resp, ts)
model_data = jmresp.model_data  # 已解密
# model_data 可能含 redirect_aid（精确匹配）或 content（模糊搜索）
if model_data.get('redirect_aid'):
    aid = model_data.redirect_aid  # 搜索直接命中的 ID
```

### 使用 jmcomic 库

```python
from jmcomic import create_option_by_file

option = create_option_by_file('config.yml')
client = option.new_jm_client()
detail = client.get_album_detail('123456')
print(detail.title)
```

**注意**: jmcomic 库内部使用 curl_cffi 并自带代理配置（mirror 的 127.0.0.1:7897）。在代理环境下 curl_cffi 对 Cloudflare 站点的 TLS 握手可能失败。此时可改用 `requests` + 直连 `cdnutc.me` 的方式手动调用 API。

### jmcomic 库的代理配置问题

jmcomic v2.7.0 默认配置的 proxy 是 `127.0.0.1:7897`，使用 `curl_cffi` 作为 postman 后端。在代理不稳定时：
- 创建自定义配置 YAML，改用 `requests` 而非 `curl_cffi`
- 指定直连域名 `domain: [jmapi: www.cdnutc.me]`
- 注意：jmcomic 启动时会自动从 setting 接口更新域名列表，覆盖手动指定的 domain

## 使用 curl_cffi 绕过 Cloudflare

当直接连 API 被 Cloudflare 拦截时，可以用 curl_cffi 的 `impersonate` 参数模拟浏览器 TLS 指纹：

```python
from curl_cffi import requests

# ⚠️ 代理必须传 dict（不能传字符串！）
proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None

resp = requests.get(
    url,
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 ..."},
    proxies=proxies,
    impersonate="chrome120",   # 关键：模拟浏览器 TLS 指纹
    timeout=15
)
```

**⚠️ 注意事项**:
- `proxies` 参数**必须传 dict** `{"http": ..., "https": ...}`，传字符串会报 `AttributeError: 'str' object has no attribute 'get'`
- `impersonate` 可选值: `"chrome120"`, `"firefox120"` 等
- 代理环境下的 TLS 兼容性取决于代理节点，某些节点会导致 `curl: (35) TLS connect error`
- 海外的代理节点对 nhentai/18comic 等 Cloudflare 站点的 TLS 兼容性可能不如国内节点

## APK 下载（Android 端）

用户问"要禁漫天堂APK"时，GitHub 上有专门的 APK 仓库：

| 项目 | Stars | 说明 |
|------|-------|------|
| [hect0x7/JMComic-APK](https://github.com/hect0x7/JMComic-APK) | ★5350 | **官方原版 APK**，最新 v2.0.26（26MB） |
| [Tom6814/JMComic3-APK-NO-Ads](https://github.com/Tom6814/JMComic3-APK-NO-Ads) | ★68 | 去广告/去游戏/去更新版 |
| [deretame/Breeze](https://github.com/deretame/Breeze) | ★1622 | 多源聚合阅读器（含禁漫、哔咔等） |
| [niuhuan/jenny](https://github.com/niuhuan/jenny) | ★1116 | JMComic 专用漫画浏览器，跨平台 |

查找 APK 流程：
1. 搜索对应仓库的 **Releases** 页
2. 下载 `.apk` 文件（arm64-v8a 对应主流安卓手机）
3. 若用户问"有没有单独的禁漫APK" — `hect0x7/JMComic-APK` 就是最纯净的

**注意**: `JMComic-APK` 在 GitHub API 搜 `jmcomic + android` 可能不出现（描述不含 android），需要用 `hect0x7/JMComic-APK` 直查。

### GitHub Release 下载（国内环境）

国内服务器下载 GitHub Release 文件时：
1. **mihomo 代理**下 GitHub 的 TLS 连接可能失败（TLS connect error / curl 35）
2. 通过 **ghproxy.net** 镜像可以下载（Azure CDN，国内能直连）
3. 推荐用 **aria2c** 多线程下载（比 curl 快得多）：
   ```bash
   aria2c -x 8 -s 8 -k 1M \
     "https://ghproxy.net/https://github.com/hect0x7/JMComic-APK/releases/download/2.0.26/2.0.26.apk"
   ```

## mihomo 代理排坑

### 代理出口 IP 验证
通过代理访问 `https://httpbin.org/ip`，检查返回的 IP 是否为代理节点 IP（而非服务器本机 IP）。如果返回服务器本机 IP，说明代理配置未生效。

### 常见 TLS 错误
- `curl: (35) TLS connect error` / `OPENSSL_internal:invalid library` — 代理节点与目标服务器的 TLS 协商失败，通常需要更换节点
- `SSL: UNEXPECTED_EOF_WHILE_READING` — 目标服务器断连，GFW 阻断或 Cloudflare 拦截
- 某些 vmess 节点对特定 CDN（Cloudflare、AWS CloudFront）有兼容问题

### 代理节点切换
当默认节点失效时，可通过修改 mihomo config.yaml 中的 `proxy-groups[].proxies` 顺序或通过 external-controller API 切换。如果没有启用 external-controller，需要手动编辑 config.yaml 并重启 mihomo。

## 已知限制

- 搜索结果 API (`/search?q=`) 返回加密数据，需要 `JmApiResp` 解密
- 无有效 token 时 API 返回空数据或 403
- token 有时效性（由时间戳生成）
- API 返回 `{"code":200,"data":[]}` 表示该 ID 在禁漫天堂 API 中无数据（但不一定代表 ID 完全不存在 — search 可能返回 redirect 而 album 接口返回空）
- 搜索时的 `redirect_aid` 字段表示精确匹配，此时 `content` 为空数组

## 参考

- jmcomic Python 库: https://github.com/hect0x7/JMComic-Crawler-Python
- jmcomic APK 原版: https://github.com/hect0x7/JMComic-APK
- curl_cffi: https://github.com/yifeikong/curl_cffi
- ghproxy (GitHub 国内加速): https://ghproxy.net
