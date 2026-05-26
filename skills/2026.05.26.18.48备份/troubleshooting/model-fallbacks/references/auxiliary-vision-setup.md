# 辅助视觉模型配置指南

## 适用场景

主聊天模型（如 DeepSeek）不支持视觉，但需要 `vision_analyze` 看图。

## 架构

```
用户发图 → Hermes vision_analyze → 检测 auxiliary.vision 配置
  → 走视觉模型 API（与主聊天模型独立）
  → 返回分析结果到对话中
```

主聊天模型不换，视觉自动路由到专用模型。

## 配置步骤

### 1. 确保有可用视觉模型

方法一：通过本地 API 中转站路由到第三方（如阿里百炼 qwen-vl-plus）
方法二：直接用 OpenRouter/SiliconFlow 等支持视觉的 provider

### 2. 配置 Hermes

```bash
hermes config set auxiliary.vision.provider "custom:apirelay"
hermes config set auxiliary.vision.model "qwen-vl-plus"       # 视觉模型名
hermes config set auxiliary.vision.base_url "http://127.0.0.1:8848/v1"
hermes config set auxiliary.vision.api_key "sk-xxx"
```

### 3. 注册 provider（config.yaml）

```yaml
providers:
  apirelay:
    base_url: http://127.0.0.1:8848/v1
    api_key: sk-xxx
    model: qwen-vl-plus
```

### 4. 验证

```bash
# 重启 gateway
hermes gateway restart
```

发送一张图片给 Hermes，`vision_analyze` 应自动走视觉模型。

## 推荐视觉模型

| 模型 | 来源 | 特点 |
|------|------|------|
| qwen-vl-plus | 阿里百炼 | 中文优化，便宜，稳定 |
| qwen2.5-vl-72b | 阿里百炼 | 更强，更贵 |
| claude-sonnet-4 | Anthropic | 原生多模态 |

## Pitfalls

- `hermes config set` 存值后需确认 config.yaml 正确，有时需要手动补 provider 注册
- SiliconFlow 的视觉模型默认禁用，需去控制台手动开通（`30003 Model disabled`），不建议
- 重启 gateway 才能生效
- 视觉模型不计入主聊天 token 费用（独立计费）
