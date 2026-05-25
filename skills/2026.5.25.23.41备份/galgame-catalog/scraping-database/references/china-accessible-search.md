# 中国网络环境下可用的 Web 搜索源

当 WSL / 国内网络环境下 Google / DuckDuckGo / Bing 国际版超时不可用时，使用这些源进行快速搜索和信息抓取。

## 📚 百科类（背景/设定/制作信息）

### 百度百科 — 首选
```
curl -sL "https://baike.baidu.com/item/URL编码词条名" \
  -H "User-Agent: Mozilla/5.0" -o /tmp/baike.html
```
- 优点：中文内容最全、访问最稳，几乎不会超时
- 爬取难度低，直接用 `curl` + 正则提取即可
- 提取规则：`<h1>` → 标题，`class="lemma-summary"` → 简介

### 中文维基百科 — 备选
```
https://zh.wikipedia.org/wiki/词条名
```
- 信息更中立、来源可追溯
- WSL 下访问速度比百度百科慢，作为备选

## 🎬 番剧/动漫信息

### Bangumi（番组计划）
```
https://bangumi.tv/subject_search/关键词
```
- 页面结构简单，curl 配合正则提取评分/简介/声优
- 中文用户首选番剧数据库

### 哔哩哔哩
```
https://www.bilibili.com
```
- 番剧页面包含简介、评分、标签

## 📰 新闻资讯类

### 新华网 / 人民网 / 央视网
```
https://www.news.cn
https://www.people.com.cn
https://tv.cctv.com
```
- 结构清晰，curl 爬取几乎不会被反爬拦截
- 适合查官方发布的权威内容

## 🔍 通用搜索

### 百度搜索
```
curl "https://www.baidu.com/s?wd=关键词" -H "User-Agent: ..."
```

### 必应国内版
```
curl "https://cn.bing.com/search?q=关键词" -H "User-Agent: ..."
```

## 💡 实用技巧

1. **先用百度百科查核心信息**（最快最稳），再用 Bangumi/维基补充
2. **User-Agent 必须伪装**：`Mozilla/5.0 (Windows NT 10.0; Win64; x64)`
3. **提取规则用 Python + re**：`re.sub(r'<[^>]+>', ' ', html)` 去标签后按句号分段
4. **遇到超时直接换源**，不要反复重试同一个不可达的境外服务
