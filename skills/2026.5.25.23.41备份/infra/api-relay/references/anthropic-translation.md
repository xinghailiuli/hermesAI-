# Anthropic Messages API 翻译层

中转站的 `/v1/messages` 端点将 Anthropic Messages API 格式翻译为 OpenAI Chat
Completions 格式，使 Claude Code 等 Anthropic 客户端能通过 DeepSeek 等 OpenAI
兼容后端运行。

**状态**：✅ 非流式 + 流式均已实现并验证通过（2026-05-25）。

## 端点

```
POST /v1/messages
```

接受 Anthropic Messages API 请求，内部翻译后转发到上游 OpenAI 兼容端点。

## 认证

支持两种认证头（`before_request` 中间件已更新）：

```
Authorization: Bearer sk-local-apirelay-2026   # OpenAI 标准
x-api-key: sk-local-apirelay-2026              # Anthropic 标准
```

Claude Code 默认发送 `x-api-key`，而非 `Authorization: Bearer`。

## 模型映射

Claude Code 发送 Anthropic 模型名（如 `claude-sonnet-4-6`），需映射到中转站实际模型。

**实现方式**（在 `anthropic_messages()` 路由处理器中）：

```python
model_id = data.get('model', 'deepseek-chat')
# Claude/Anthropic 模型名直接映射
if 'claude' in model_id.lower() or 'anthropic' in model_id.lower():
    model_id = 'deepseek-chat'
cfg = get_model_config(model_id)
```

⚠️ **为什么不依赖 config.json 通配**：`get_model_config()` 的 DashScope passthrough
回退会将未知模型名作为 `upstream_model` 发给 DashScope，导致 DeepSeek 被调但不返回内容
（`input_tokens: 0, output_tokens: 0`）。必须先做 Claude→DeepSeek 映射再查 config。

`config.json` 的 `anthropic_model_map` 字段也支持更细粒度映射（可选）：

```json
{
  "anthropic_model_map": {
    "claude-sonnet-4-6": "deepseek-chat",
    "claude-opus-4-5": "deepseek-reasoner"
  },
  "default_anthropic_model": "deepseek-chat"
}
```

未匹配的模型名回退到 `default_anthropic_model`。

## 请求翻译：Anthropic → OpenAI

`anthropic_to_openai()` 函数处理以下转换：

| Anthropic 字段 | OpenAI 字段 | 说明 |
|---|---|---|
| `model` | `model` | 通过 `anthropic_model_map` 映射 |
| `system` (string or array) | `messages[0]` (role=system) | 数组格式 `[{type:"text",text:...}]` 自动拼接 |
| `messages[].content` (array) | `messages[].content` (string) | 提取 `type:"text"` 块拼接，`type:"tool_use"` 转 `tool_calls` |
| `messages[].content[type=tool_result]` | `messages[]` (role=tool) | 含 `tool_use_id` |
| `max_tokens` | `max_tokens` | 直接映射 |
| `temperature`, `top_p`, `top_k` | 同名字段 | 直接映射 |
| `stop_sequences` | `stop` | 数组→数组 |
| `stream` | `stream` | 直接映射 |
| `tools[]` (input_schema) | `tools[].function.parameters` | Anthropic 用 `input_schema`，OpenAI 用 `parameters` |

### Assistant 消息中 tool_use 的处理

Anthropic assistant 消息的 `content` 数组可同时含 `text` 和 `tool_use` 块：

```json
{"role": "assistant", "content": [
  {"type": "text", "text": "Let me check..."},
  {"type": "tool_use", "id": "toolu_xxx", "name": "get_weather", "input": {"city": "NYC"}}
]}
```

转为 OpenAI：
```json
{"role": "assistant", "content": "Let me check...", "tool_calls": [
  {"id": "toolu_xxx", "type": "function", "function": {"name": "get_weather", "arguments": "{\"city\":\"NYC\"}"}}
]}
```

注意：`input` 是 dict 对象，需 `json.dumps()` 转为字符串。

## 响应翻译：OpenAI → Anthropic（非流式）

`openai_to_anthropic()` 函数处理：

| OpenAI 字段 | Anthropic 字段 | 说明 |
|---|---|---|
| `choices[0].message.content` | `content[0].text` | `type: "text"` |
| `choices[0].message.tool_calls[]` | `content[]` (type=tool_use) | `arguments` JSON 反序列化回 dict |
| `choices[0].finish_reason` | `stop_reason` | `stop`→`end_turn`, `length`→`max_tokens`, `tool_calls`→`tool_use` |
| `usage.prompt_tokens` | `usage.input_tokens` | |
| `usage.completion_tokens` | `usage.output_tokens` | |

响应格式示例：
```json
{
  "id": "...",
  "type": "message",
  "role": "assistant",
  "content": [{"type": "text", "text": "Hello!"}],
  "model": "claude-sonnet-4-6",
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "usage": {"input_tokens": 9, "output_tokens": 2}
}
```

## 响应翻译：OpenAI SSE → Anthropic SSE（流式）

Claude Code 默认使用流式（`stream: true`）。Anthropic SSE 格式与 OpenAI 完全不同，需要完整的**事件序列**：

```
event: message_start
data: {"type":"message_start","message":{"id":"msg_xxx","type":"message","role":"assistant","model":"...","content":[],"usage":{"input_tokens":0}}}

event: content_block_start
data: {"type":"content_block_start","index":0,"content_block":{"type":"text","text":""}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":"Hello"}}

event: content_block_delta
data: {"type":"content_block_delta","index":0,"delta":{"type":"text_delta","text":" world"}}

event: content_block_stop
data: {"type":"content_block_stop","index":0}

event: message_delta
data: {"type":"message_delta","delta":{"stop_reason":"end_turn","stop_sequence":null},"usage":{"output_tokens":5}}

event: message_stop
data: {"type":"message_stop"}
```

**关键点**：
- 每个事件必须带 `event:` 行前缀
- 每个 data 必须是单行 JSON（不是多行）
- 事件之间用空行分隔
- 缺失 `event:` 行或格式不正确 → Claude Code 静默超时

### 当前实现

`anthropic_stream_response()` 生成器产生完整事件序列：

1. `message_start` — 包含消息 ID、空 content 数组
2. `content_block_start` — 索引 0 的文本块
3. `ping` — Anthropic 要求的保活事件
4. `content_block_delta` × N — 逐 token 输出（`text_delta` 类型）
5. `content_block_stop` — 文本块结束
6. `message_delta` — stop_reason + usage
7. `message_stop` — 流结束标志

**已验证**：curl 测试流式输出正常，事件格式被 Claude Code 兼容。

### 测试命令

```bash
# 非流式
curl -s -X POST http://localhost:8848/v1/messages \
  -H "x-api-key: sk-local-apirelay-2026" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","max_tokens":50,"messages":[{"role":"user","content":"Hello"}],"stream":false}'

# 流式
curl -s -N -X POST http://localhost:8848/v1/messages \
  -H "x-api-key: sk-local-apirelay-2026" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","max_tokens":50,"messages":[{"role":"user","content":"Hello"}],"stream":true}'
```

## Claude Code 配置

```bash
# ⚠️ ANTHROPIC_BASE_URL 不要包含 /v1 — Claude Code 内部自动追加 /v1/messages
export ANTHROPIC_BASE_URL="http://localhost:8848"
export ANTHROPIC_API_KEY="sk-local-apirelay-2026"
claude --bare --model claude-sonnet-4-6 -p "your prompt"
```

`--bare` 模式跳过 OAuth/keychain 读取，强制使用环境变量中的 `ANTHROPIC_API_KEY`。

### Pitfall: ANTHROPIC_BASE_URL 双写 /v1

若设为 `http://localhost:8848/v1`，Claude Code 发出的实际请求为
`POST /v1/v1/messages?beta=true` → 405 Method Not Allowed。中转站日志会显示
`"POST /v1/v1/messages?beta=true HTTP/1.1" 405`。

正确写法永远是 `http://host:port`（不带路径后缀）。

### 永久配置

将环境变量写入 `~/.bashrc` 使新 shell 自动加载：

```bash
echo 'export ANTHROPIC_BASE_URL="http://localhost:8848"' >> ~/.bashrc
echo 'export ANTHROPIC_API_KEY="sk-local-apirelay-2026"' >> ~/.bashrc
```

## Pitfalls

### `call_upstream` 流式返回值 bug（已修复，防御性记录）

**症状**：Claude Code 请求到达中转站、`[Anthropic]` 日志正常打印，但流式响应始终为空 / 超时。转用 curl 测试非流式 `/v1/messages` 正常，但流式返回 500。

**根因**：`call_upstream()` 对流式请求返回 `(resp, stream)`，其中 `stream` 是布尔值 `True` 而非 HTTP 状态码。调用方检查 `status_code != 200` 时 `True != 200` 为真，误入错误处理分支，试图 `jsonify(resp)` 导致 `TypeError: Object of type Response is not JSON serializable`。

**修复**：`call_upstream` 第 97 行：
```python
# 错误（修复前）
if stream:
    return resp, stream       # → (Response, True)  ← BUG!

# 正确（修复后）
if stream:
    return resp, resp.status_code   # → (Response, 200)
```

**教训**：流式/非流式分支的返回值语义必须一致 — 调用方永远期望 `(data_or_resp, http_status_code)`。

### Anthropic SSE 格式缺失 `event:` 行 → Claude Code 静默超时

Anthropic SSE 要求每条数据前有 `event:` 行（如 `event: content_block_delta`），仅 `data:` 行不够。OpenAI SSE 只用 `data:` 行。缺失 `event:` 行时 curl 能看到返回但 Claude Code 不识别，表现为静默超时无任何错误。

### Claude Code 默认 max_tokens=32000

Claude Code 发送的 `max_tokens` 默认高达 32000，可能超出上游模型限制。翻译层目前直接透传此值，如需限制可在 `anthropic_to_openai()` 中添加 `min(anthropic_body.get('max_tokens', 32000), MAX_LIMIT)`。

### 调试流式问题

1. 先用 curl 测非流式 `/v1/messages`（确认翻译链正常）
2. 再用 curl 测流式（确认 SSE 事件序列完整）
3. 中转站日志中 `[Anthropic]` 出现但无后续 → 请求成功到达但翻译/转发环节失败
4. 中转站日志中既无 `[Anthropic]` 也无错误 → 请求未到达（检查端口/认证）
