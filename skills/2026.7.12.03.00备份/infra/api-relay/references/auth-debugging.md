# API 中转站 Auth 调试

## Auth 机制

server.py 的 `check_auth()` 函数支持两种认证方式：

1. `Authorization: Bearer <token>` — 标准 OpenAI 格式
2. `x-api-key: <token>` — 备用 header

Token 来源：`config.json` → `auth.local_token`

## 端点权限

| 端点 | 需要 Auth | 说明 |
|------|-----------|------|
| `/health` | ❌ 不需要 | 返回 `{"status":"ok","models":6}` |
| `/stats` | ✅ 需要 | 请求统计 |
| `/v1/models` | ✅ 需要 | 模型列表 |
| `/v1/chat/completions` | ✅ 需要 | 聊天 |
| `/v1/messages` | ✅ 需要 | Anthropic 兼容 |
| `/v1/responses` | ✅ 需要 | Codex Responses API |

## 调试流程

### 1. 确认中转站在运行

```bash
ps aux | grep relay | grep -v grep
# 或
curl -s 127.0.0.1:8848/health
```

如果 health 返回 ok 但 auth 端点 401 → token 问题。

### 2. 确认是 systemd 还是裸进程

```bash
systemctl --user status api-relay 2>&1
# Unit not found → 裸进程，用 ps 检查
# Loaded/Active → systemd 管理
```

### 3. Token 截断排查（关键！）

当工具显示 `sk-loc...2026` 时，**不要假设这是 literal `...`**。
Hermes 工具链会截断中等长度字符串（安全 redaction）。

**诊断方法 — 用 hex/bytes 读取绕过截断：**

```bash
# 方法 1：Python bytes 读取（最可靠）
python3 -c "
with open('/home/admin/api-relay/config.json','rb') as f:
    data = f.read()
idx = data.find(b'sk-loc')
print(repr(data[idx:idx+30].decode()))
"

# 方法 2：直接读 JSON 并输出长度
python3 -c "
import json
c = json.load(open('/home/admin/api-relay/config.json'))
token = c['auth']['local_token']
print(f'Token: {token}')
print(f'Length: {len(token)}')
"
```

### 4. Codex 专用：检查 CODEX_API_KEY 长度

Codex 通过 `CODEX_API_KEY` 环境变量传递 token。如果与中转站
`local_token` 长度不一致，必然 401：

```bash
python3 -c "
import json, os
c = json.load(open('/home/admin/api-relay/config.json'))
print(f'Flask token length: {len(c[\"auth\"][\"local_token\"])}')
print(f'CODEX_API_KEY length: {len(os.environ.get(\"CODEX_API_KEY\",\"\"))}')
"
```

长度不一致 → `export CODEX_API_KEY="<完整token>"` 修正。

### 5. 用 Python requests 验证（绕过 shell 转义问题）

curl 可能在 shell 中错误转义 token。用 Python 直接测试：

```bash
python3 -c "
import json, requests
config = json.load(open('/home/admin/api-relay/config.json'))
token = config['auth']['local_token']
r = requests.get('http://127.0.0.1:8847/v1/models',
    headers={'Authorization': f'Bearer {token}'})
print(f'Status: {r.status_code}, Body: {r.text[:200]}')
"
```

### 6. 测试 x-api-key 备用 header

```bash
python3 -c "
import json, requests
config = json.load(open('/home/admin/api-relay/config.json'))
token = config['auth']['local_token']
r = requests.get('http://127.0.0.1:8847/v1/models',
    headers={'x-api-key': token})
print(f'Status: {r.status_code}')
"
```

### 7. codex doctor 查看路由探测结果

```bash
codex doctor 2>&1 | grep -A5 'reachability'
```

关键指标：
- `openai API base URL ... reachable (HTTP 404)` — 基础 URL 可达
- `openai API route probe ... (HTTP 401)` — **auth 不匹配**
- `openai API route probe ... (HTTP 200)` — ✅ 认证通过
