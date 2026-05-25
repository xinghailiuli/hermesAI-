# Hermes Web Search 配置

当服务器无法直接访问某些网站时（GFW/CDN/DPI 过滤），Web Search 可以间接获取信息。

## 支持的后端

| 后端 | 免费额度 | 需要注册 | 配置方式 |
|------|:--:|:--:|------|
| **DDGS** | 无限 | ❌ | `pip install ddgs` + `web.backend: ddgs` |
| **Tavily** | 1000次/月 | ✅ | `TAVILY_API_KEY` 环境变量 |
| **Brave Search** | 2000次/月 | ✅ | `BRAVE_SEARCH_API_KEY` 环境变量 |
| **SearXNG** | 无限 | ❌ 自建 | `SEARXNG_URL` 环境变量 |
| Firecrawl | 付费 | ✅ | `FIRECRAWL_API_KEY` |
| Exa | 付费 | ✅ | `EXA_API_KEY` |
| Parallel | 付费 | ✅ | `PARALLEL_API_KEY` |

## 最快方案：DDGS（零配置）

```bash
# 1. 安装
pip install ddgs

# 2. 在 ~/.hermes/config.yaml 添加：
# web:
#   backend: ddgs

# 3. 重启网关
sudo systemctl restart hermes-gateway
```

## 配置结构（config.yaml）

```yaml
web:
  backend: tavily          # 共用后端
  search_backend: ddgs     # 可选：搜索专用后端
  extract_backend: tavily  # 可选：提取专用后端
```

支持单独为搜索/提取指定不同后端。

## 环境变量示例

```bash
# ~/.hermes/.env
TAVILY_API_KEY=tvly-xxxxxxxx
# 或
BRAVE_SEARCH_API_KEY=BSAxxxxxxxx
# 或
SEARXNG_URL=http://your-searxng-instance:8080
```
