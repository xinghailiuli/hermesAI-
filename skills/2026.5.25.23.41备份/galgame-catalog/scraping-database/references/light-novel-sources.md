# 中国轻小说站点可访问性 & 爬取策略

> 用户只看日轻/韩轻翻译，不看国产网文（菠萝包、刺猬猫等）。

## 站点速查

| 站点 | curl | 内容类型 | 限制 | 备注 |
|------|------|----------|------|------|
| **轻之国度 lightnovel.cn** | ✅ 可用 | 日轻翻译（最新发布） | 无 | `/category/3/106?type=1` 轻小说最新 |
| **bilibili.com/v/literature** | ⚠️ 3KB空壳 | 日轻 | JS渲染 | 需要 headless，curl 只能拿到框架 |
| **bilinovel.com** | ❌ Cloudflare | 日轻在线阅读 | CF盾 | 手机UA偶尔能过一章，目录页全拦截 |
| **菠萝包 book.sfacg.com** | ✅ 可用 | 国产网文 | — | 国产，用户不需要 |
| **刺猬猫 ciweimao.com** | ✅ 可用 | 国产网文 | — | 国产，用户不需要 |
| **轻小说文库 wenku8.net** | ⚠️ 302跳转 | 日轻 | 重定向 | 可能需要cookie |
| **ESJ Zone esjzone.cc** | ❌ 超时 | 日轻/韩轻 | 无法连接 | 放弃 |
| **动漫之家 xs.dmzj.com** | ❌ 超时 | 混合 | 无法连接 | 放弃 |

## 轻之国度爬取细节

### URL 格式
- 轻小说最新：`https://www.lightnovel.cn/category/3/106?type=1`
- 整卷：`https://www.lightnovel.cn/category/3/107?type=1`
- 详情页：`https://www.lightnovel.cn/cn/detail/{ID}`（注意是 `/cn/detail/` 不是 `/detail/`）

### HTML 结构
```html
<a href="/cn/detail/1144366" title="[西条阳]不过是偶像！～但是果然颜值好高～[⚡️文库]" class="module-title">
  <span class="title">[西条阳]不过是偶像！～但是果然颜值好高～[⚡️文库]</span>
</a>
...
<div class="create-time">2 小时前</div>
```

### 提取正则
```python
items = re.findall(
    r'<a\s+href="(/cn/detail/\d+)"[^>]*title="([^"]+)"[^>]*class="module-title[^"]*"[^>]*>.*?</a>.*?create-time[^>]*>([^<]+)',
    html, re.DOTALL
)
```

### 标题解析
格式：`[作者名] 书名 卷数/章节 [文库/备注]`
```python
m = re.match(r'^\[([^\]]+)\]\s*(.+)', title)  # 提取作者
meta_m = re.findall(r'\[([^\]]+)\]$', rest)     # 提取尾部备注
```

### 过滤规则
- 跳过包含 `置顶`、`版规`、`勋章`、`工资` 的帖子
- 跳过没有作者名的条目（可能是原创或特殊格式）

### 完整脚本
`~/.hermes/scripts/lightnovel_scraper.py`

## 日轻翻译源对比

| 指标 | 轻之国度 | bilinovel (哔哩轻小说) |
|------|----------|------------------------|
| 可爬取性 | ✅ curl 直接抓 | ❌ Cloudflare |
| 内容量 | 大（日轻翻译大本营） | 中（在线阅读为主） |
| 更新频率 | 实时（每小时有新帖） | 中等 |
| 数据格式 | 结构化HTML | JS渲染 |
| 推荐 | ✅ 首选 | ❌ 放弃 |
