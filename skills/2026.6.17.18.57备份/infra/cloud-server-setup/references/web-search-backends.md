# Hermes Web Search 后端配置

配置键：`web.backend` 或 `web.search_backend`（按工具单独指定）

## 支持的后端

| 后端 | 免费 | API Key | 配置 |
|------|:--:|:--:|------|
| **ddgs** | ✅ 无限 | 无 | `pip install ddgs` |
| **tavily** | ✅ 1000/月 | TAVILY_API_KEY | env var |
| **brave-free** | ✅ 2000/月 | BRAVE_SEARCH_API_KEY | env var |
| **searxng** | ✅ 无限 | SEARXNG_URL | 自建实例 |
| firecrawl | ❌ 付费 | FIRECRAWL_API_KEY | env var |
| parallel | ❌ 付费 | PARALLEL_API_KEY | env var |
| exa | ❌ 付费 | EXA_API_KEY | env var |

## 配置示例 (config.yaml)

```yaml
web:
  backend: ddgs  # 零配置，装包即用
  # 或按工具分别指定
  # search_backend: tavily
  # extract_backend: firecrawl
```

## 环境变量

写入 `~/.hermes/.env`：
```
TAVILY_API_KEY=tvly-xxx
BRAVE_SEARCH_API_KEY=BSA-xxx
```

## DDGS 快速上手

```bash
pip install ddgs --break-system-packages
# config.yaml 加 `web: {backend: ddgs}`
# 重启网关
```

## 注意

- `ddgs` 基于 DuckDuckGo，中文搜索质量不如 Tavily
- Tavily 需要注册 https://tavily.com
- 后端自动检测：如果没设 `backend`，按环境变量自动选择（Firecrawl > Parallel > Tavily > Exa > SearXNG > Brave > DDGS）
