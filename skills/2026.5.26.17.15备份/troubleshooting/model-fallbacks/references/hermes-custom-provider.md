# 给Hermes Agent添加自定义Provider作为Fallback

## 背景
Hermes默认使用单一模型provider。当主模型（如DeepSeek）挂掉、限流或超时，可通过`fallback_providers`自动切换到备用。

## 配置方式

### 方式一：hermes config set（有坑）
```bash
hermes config set providers.PROVIDER_NAME \
  '{"base_url":"https://api.xxx.com/v1","api_key":"sk-xxx","model":"model-name"}'
hermes config set fallback_providers '["PROVIDER_NAME"]'
```
**坑**：值会被存为JSON字符串而非YAML对象。需手动修复。

### 方式二：直接编辑config.yaml（推荐）
```yaml
providers:
  siliconflow:
    base_url: https://api.siliconflow.cn/v1
    api_key: sk-yxxx
    model: deepseek-ai/DeepSeek-V3
fallback_providers:
  - siliconflow
```

## 可用平台速查

| Provider名 | base_url | 典型model |
|-----------|----------|-----------|
| siliconflow | https://api.siliconflow.cn/v1 | deepseek-ai/DeepSeek-V3 |
| deepseek | https://api.deepseek.com/v1 | deepseek-chat |
| openai | https://api.openai.com/v1 | gpt-4o |
| gemini | https://generativelanguage.googleapis.com/v1beta/openai | gemini-pro |

## 验证
```bash
hermes config check   # 检查格式
grep -A5 "providers:" ~/.hermes/config.yaml  # 确认YAML格式
```
重启Hermes后生效。主模型故障时自动切到fallback列表中的下一个。
