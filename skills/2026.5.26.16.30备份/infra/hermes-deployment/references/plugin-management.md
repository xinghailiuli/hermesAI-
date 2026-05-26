# Hermes 插件评估与安装

## 发现插件

GitHub 搜索 Hermes Agent 插件：

```bash
curl -s "https://api.github.com/search/repositories?q=hermes-agent+plugin&sort=stars&order=desc&per_page=15" \
  | python3 -c "import json,sys;data=json.load(sys.stdin);[print(f'⭐ {r[\"stargazers_count\"]}  {r[\"full_name\"]}\n   {r[\"description\"]}\n   {r[\"html_url\"]}\n') for r in data.get('items',[])]"
```

国内网络 GitHub raw 可能超时，README 用 API 获取更稳：

```bash
curl -s -H "Accept: application/vnd.github.raw" \
  "https://api.github.com/repos/<owner>/<repo>/contents/README.md"
```

## 评估标准

| 检查项 | 通过条件 |
|--------|---------|
| 语言 | Python 优先，TypeScript/HTML 看情况 |
| 依赖 | 不需要额外外部服务（Langfuse/Qdrant/MQTT/Docker）→ 拒绝 |
| API Key | 需要自行申请第三方 key → 降低优先级 |
| 更新频率 | 近一个月内有更新 |
| 与内置功能重叠 | 已有 `web_search` 就不装 `web-search-plus` |

## 安装

```bash
# 标准方式
hermes plugins install owner/repo

# 启用
hermes plugins enable <plugin-name>

# 重启网关生效
hermes gateway restart
```

## 安装后必须备份

```bash
hermes backup -o /home/admin/hermes-backups/hermes-$(date +%Y%m%d).zip
```

## Dashboard 插件注意

Dashboard 插件（如 hermes-labyrinth）安装后**不会出现在 `hermes plugins list`** 中。
它们通过 `dashboard/manifest.json` 注册，在 `hermes dashboard` 中以新选项卡形式出现。
安装时有 "doesn't contain plugin.yaml or __init__.py" 警告可忽略。

## 已验证可用的插件

| 插件 | 类型 | 作用 |
|------|------|------|
| hermes-lcm | 标准插件 | 无损上下文管理，DAG 引擎 |
| hermes-labyrinth | Dashboard 插件 | 会话轨迹/Cron/技能观测面板 |
