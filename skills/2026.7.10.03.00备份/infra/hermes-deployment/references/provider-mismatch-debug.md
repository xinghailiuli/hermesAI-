# Provider 不匹配调试实录

## 场景

网关已连接，用户发消息后回复极慢（79-152 秒），最终返回：
`API call failed after 3 retries: Connection error.` 或 `Request timed out.`

回复内容通常只有 50-51 字符（正好是错误消息本身的长度），说明**没有成功生成任何实质内容**。

## 排查路径

### 1. 确认网关连接正常
```bash
cat ~/.hermes/gateway_state.json
# qqbot: connected, weixin: connected → 平台连接层面无问题
```

### 2. 检查 API 连通性
```bash
# 直接测试 API（绕过代理）
curl https://api.deepseek.com/v1/models -H "Authorization: Bearer $OPENAI_API_KEY"
# → HTTP 200，正常

# 通过代理测试
curl -x http://127.0.0.1:7897 https://api.deepseek.com/v1/models ...
# → HTTP 200，正常
```
结论：API 和代理都不是瓶颈。

### 3. 检查 request_dump（关键步骤）
```bash
ls -lt ~/.hermes/sessions/request_dump_*.json
```

查看最近一个 dump：
```python
d['request']['url']      # → https://openrouter.ai/api/v1/chat/completions ❌
d['request']['body']['model']  # → deepseek-v4-pro
d['error']['type']       # → APITimeoutError
d['error']['message']    # → Request timed out.
```

**关键发现**：请求发到了 `openrouter.ai` 而不是期望的 `api.deepseek.com`。

### 4. 根因分析：OPENAI_API_KEY 自动检测陷阱

即使 `config.yaml` 中**没有指定** `provider: openrouter`，网关仍可能解析为 openrouter。
这是因为 `auth.py` 的 `resolve_provider()` 有自动检测逻辑：

```
优先级（当 provider 未显式指定或为 "auto" 时）：
1. auth.json 中的 active_provider
2. 显式 CLI api_key/base_url → "openrouter"
3. OPENAI_API_KEY 或 OPENROUTER_API_KEY 环境变量 → "openrouter"  ← 陷阱所在
4. 特定 Provider 的 API key → 对应 provider
5. 兜底： "openrouter"
```

只要 `.env` 中有 `OPENAI_API_KEY`（即使 key 是 DeepSeek 的），自动检测就会把 provider 解析为 "openrouter"，
然后网关往 `openrouter.ai` 发请求。OpenRouter 不认 OpenAI/DeepSeek 的 key → Connection error / Timeout。

### 5. 修复方案：custom_providers 显式路由

既然自动检测会把 `OPENAI_API_KEY` 映射到 openrouter，就必须用 `custom_providers`
显式注册一个指向正确 API 端点的 provider，然后让 `model.provider` 指定它：

```yaml
# ~/.hermes/config.yaml
model:
  default: deepseek-v4-pro
  provider: custom:deepseek          # 显式指定自定义 provider

custom_providers:
  - name: deepseek
    base_url: https://api.deepseek.com/v1
    key_env: OPENAI_API_KEY          # 复用 .env 中已有的 key
    api_mode: openai_chat
```

这样网关会直接向 `api.deepseek.com/v1` 发请求，完全绕过 openrouter 的自动检测。

### 6. 为什么仅去 `provider` 行不够

仅从 config.yaml 删除 `provider: openrouter` 行（不设 `custom_providers`）：
- 自动检测仍然启动 → 仍然解析为 openrouter
- 但 openrouter 没有有效 key → 仍然 Connection error / Timeout
- request_dump 中的 URL 仍然是 `openrouter.ai`

必须用 `custom_providers` + 显式 `model.provider` 才能彻底绕过自动检测。

### 7. 旧会话保留旧 provider

即使修改 config.yaml 并重启网关，**已存在的会话文件在创建时锁定了 provider**，
不会自动更新。需删除旧会话让下一条消息创建新会话：

```bash
mv ~/.hermes/sessions/<session_id>.jsonl ~/.hermes/sessions/<session_id>.jsonl.bak
```

## 代理配置

网关 systemd service 的代理覆盖文件：
```
/home/admin/.config/systemd/user/hermes-gateway.service.d/proxy.conf
```
内容：
```ini
[Service]
Environment="HTTP_PROXY=http://127.0.0.1:7897"
Environment="HTTPS_PROXY=http://127.0.0.1:7897"
```

网关**始终通过此代理**出站，CLI 会话也继承相同代理环境变量。

## 辅助 LLM 配置

上下文压缩摘要需要单独的辅助模型配置：
```yaml
auxiliary:
  compression:
    provider: openai
    model: gpt-4o-mini
```

如果只有 `OPENAI_API_KEY` 没有 OpenRouter key，用 `provider: openai` 即可，
无需额外 API key。
