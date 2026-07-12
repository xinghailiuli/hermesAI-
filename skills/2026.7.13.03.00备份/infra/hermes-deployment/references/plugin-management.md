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

## 高星插件分析参考（2026.5.26）

| 插件 | ⭐ | 判断 |
|------|------|------|
| hermes-lcm | 592 | ✅ 无损上下文，SQLite+DAG，Python 无外部依赖 |
| hermes-labyrinth | 277 | ✅ Dashboard 观测面板，搭配 cron 用 |
| web-search-plus | 194 | ❌ 需自备多个搜索 API key，内置搜索已够用 |
| maestro | 174 | ❌ TypeScript 重型代码代理，非 Hermes 原生 |
| evey-plugins | 148 | ❌ 23 插件全家桶，依赖 Langfuse+Qdrant+Docker |
| icarus-plugin | 122 | ❌ 自记忆+模型替换，偏机器学习训练场景 |
| cronalytics | 73 | 可选 — cron 分析面板，适合多 cron 用户 |
| LangBot | 16k | ❌ Hermes Gateway 替代品，非插件。装了会丢失 cron/session/memory/skills。仅在当前 QQ 网关不稳时才考虑 |

## 非插件项目分析（可能会被误认为是插件）

### LangBot (16k⭐)

LangBot 是一个独立的 QQ/微信/飞书 机器人平台，**不是 Hermes 插件**。它用自己的网关替代 Hermes Gateway。

| 优势 | 劣势 |
|------|------|
| Web 管理面板（GUI 配置） | ❌ 丢失 Hermes cron 定时任务 |
| 数百个插件市场 | ❌ 丢失 Hermes session 记忆 |
| 原生支持 QQ 官方 API | ❌ 丢失 skills 工作流 |
| 企业级敏感词/限流/监控 | ❌ 丢失 memory 系统 |
| 内置 RAG 知识库 + Dify 集成 | ❌ 丢失 tool calling 原生能力 |

**结论**：当前 Hermes QQ Gateway 稳定运行时不建议迁移。LangBot 适合从零搭建 QQ 机器人，不适合已有 Hermes 深度集成的场景。

### claude-mem (78k⭐)

claude-mem 是 Claude Code/Cursor 等 IDE 的持久化内存压缩插件，**不是 Hermes 插件**。描述中声称支持 Hermes，但实际只适用于交互式编码 IDE。

| 判断 | 原因 |
|------|------|
| ❌ 不安装 | 需要 Bun 运行时 + `npx claude-mem install` 初始化，是 IDE 插件非 MCP 服务 |
| ❌ 不安装 | Hermes 内置 memory + session_search + hermes-lcm 已有同等能力 |

### manifest (6.6k⭐)

manifest 是智能模型路由 Docker 服务，OpenAI 兼容 API 代理。**不是 Hermes 插件**。

| 判断 | 原因 |
|------|------|
| ❌ 不安装 | 纯 Docker 镜像，需要 Docker 环境 |
| ❌ 不安装 | 与已有 API 中转站功能重叠（中转站已实现模型路由和 fallback） |

### npm 镜像加速（国内服务器）

npm 官方源从国内访问可能超时 60s+，用 npmmirror 镜像：

```bash
npm install -g <package> --registry=https://registry.npmmirror.com
```

仅用于非 Hermes 插件的 npm 工具安装，Hermes 插件一律用 `hermes plugins install`。
