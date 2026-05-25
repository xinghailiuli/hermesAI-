# 中文网络搜索/浏览 替代方案

当从 WSL/中国网络环境下 web_search 超时或 curl Google/Bing 不可用时，转用以下中文站点。这些站在国内延迟低，`curl` 配合 `grep` / `python3` 正则即可提取内容。

## 百科类

### 百度百科 (baike.baidu.com)
最稳定、最全的中文内容源。适用于查动漫、轻小说、人物、影视词条。

```bash
# 编码后的URL关键词
curl -sL "https://baike.baidu.com/item/%E6%B0%B8%E8%BF%9C%E7%9A%84%E9%BB%84%E6%98%8F" \
  -H "User-Agent: Mozilla/5.0" -o /tmp/baike.html
```

提取技巧（Python3）：
- 标题：`r'<h1[^>]*>(.*?)</h1>'`
- 简介：`r'class="lemma-summary"[^>]*>(.*?)</div>'`
- 通用清洗：`re.sub(r'<[^>]+>', ' ', text)` + `re.sub(r'\s+', ' ', text)`

### 中文维基百科 (zh.wikipedia.org)
更中立、来源可追溯，访问速度略慢于百度百科。

## 轻小说/动漫

### 轻之国度 (lightnovel.cn / lightnovel.fun)
轻小说排行榜、新闻、翻译连载。首页即含排行。

### 轻小说文库 (wenku8.net)
轻小说目录和热门作品列表。需注意编码（gbk）。

### 番组计划 (bangumi.tv)
动漫评分、信息，页面结构简单适合 curl 提取。

## 搜索类

### 百度搜索
`https://www.baidu.com/s?wd=关键词`
结果较少但访问稳定。

### 必应国内版
`https://cn.bing.com/search?q=关键词`

## 常见技巧

1. **总是加 UA**：`-H "User-Agent: Mozilla/5.0"` 避免被反爬
2. **编码URL**：中文关键词需 URL 编码，Python 用 `urllib.parse.quote()`
3. **超时设置**：`--connect-timeout 10 -m 15` 防止无限等待
4. **解码优先**：先试 utf-8，失败再试 gbk/gb2312
5. **仅提取文本**：`re.sub(r'<[^>]+>', ' ', content)` 快速去标签

## 已知限制

- **百度搜索** 偶尔超时（~15秒），但百度百科几乎不会
- **轻之国度** 首页内容适合用 `关键词` 定位（小说、排行、连载）
- **WSL下** 访问境外站（Google, DuckDuckGo）通常超时，不推荐
