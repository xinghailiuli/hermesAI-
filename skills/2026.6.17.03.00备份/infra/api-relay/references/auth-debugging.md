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

### 3. Token 截断排查（见 SKILL.md Pitfalls）

当工具显示 `sk-loc...2026` 时，**不要假设这是 literal `...`**。用 hex/bytes 验证真实 token。

### 4. 测试 auth

```bash
# 成功：HTTP 200 + 模型列表
curl -s -w "\nHTTP:%{http_code}" 127.0.0.1:8848/v1/models \
  -H "Authorization: Bearer <完整token>"

# 失败排查：尝试 x-api-key header
curl -s -w "\nHTTP:%{http_code}" 127.0.0.1:8848/v1/models \
  -H "x-api-key: <完整token>"
```
