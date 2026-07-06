# QQ 端点运维操作

## 快速状态检查

```bash
# 查看最近 QQ 日志
grep -i "qq" ~/.hermes/logs/gateway.log | tail -8
```

期望输出（在线）：
```
INFO gateway.run: Connecting to qqbot...
INFO ... Access token refreshed, expires in NNNNs
INFO ... Gateway URL: wss://api.sgroup.qq.com/websocket
INFO ... WebSocket connected ...
INFO ... Connected
INFO gateway.run: ✓ qqbot connected
INFO ... Identify sent
INFO ... Ready, session_id=...
```

## 重启 QQ 端点

网关进程可能有两个来源：
1. admin 用户启动的（正常）
2. root 用户残留的（僵尸，`--replace` 无法自动清理）

### 实操流程（本次会话验证）

```bash
# Step 1: 杀掉当前网关
kill $(cat ~/.hermes/gateway.pid | jq -r .pid) 2>/dev/null

# Step 2: 找 root 残留进程并清理
ps aux | grep "gateway run" | grep root | grep -v grep | awk '{print $2}' | xargs -r sudo kill -9

# Step 3: 确认清空
ps aux | grep "gateway run" | grep -v grep   # 应无输出

# Step 4: 重新启动
hermes gateway run --replace &

# Step 5: 验证
sleep 3
grep -i "qq" ~/.hermes/logs/gateway.log | tail -5
```

## 关键指标

| 指标 | 正常值 | 异常处理 |
|-----|--------|---------|
| WebSocket 连接 | Connected + Ready | 检查 key/secret 配置 |
| Session timeout | 每 30 分钟一次，自动重连 2-5s | 正常行为，无需处理 |
| Token 过期 | 约 6000s，自动刷新 | 出现 401 则需人工检查凭证 |
| 连续重连失败 3 次+ | 不应出现 | 人工介入 |

## 会话记录

### 2026-05-27 20:47 — 双进程竞争 + 模型未配置

**两次诊断路径**：

**第 1 轮：重启 QQ 端点**
- 操作：kill admin PID 15245 + root PID 4400，重启 `hermes gateway run --replace`
- 结果：1s 内 Ready，新 session_id=3cfa2b60
- 教训：root 僵尸进程需 `sudo kill -9`

**第 2 轮："还是没回我"（Ready 但不响应）**
- 现象：Bot 显示 Ready，用户发消息后不回
- 诊断：`ps aux | grep gateway` 发现 **两个** 网关进程（root PID 16199 + admin PID 16321）
- 根因：双进程竞争同一个 QQ WebSocket，都 Ready，但消息分发线程卡死
- 修复：`sudo kill -9 16199 16321`，重新启动单个网关
- 结果：再次 Ready，开始接收消息

**第 3 轮："还是没回我"（Ready 但回复是错误信息）**
- 现象：Bot 收到消息并回复了，但回复内容是错误而非 agent 回答：
  ```
  ⚠ No auxiliary LLM provider configured
  ❌ HTTP 400: ... but you passed .   ← 模型名为空
  ```
- 诊断：`cat ~/.hermes/config.yaml` 只有 onboarding，没有 model 配置
- 根因：`.env` 有 OPENAI_API_KEY + OPENAI_BASE_URL 指向 DeepSeek，但 gateway 从 config.yaml 读模型名，读到空字符串
- 修复：在 config.yaml 添加：
  ```yaml
  model:
    default: deepseek-v4-pro
    provider: openrouter
  ```
- 重启网关后正常回复（160 chars, 22.5s）

**总结**：QQ Bot "Ready 但不回" 有三类根因：
1. 旧 root 僵尸进程 — `sudo kill -9`
2. 双网关竞争 — 杀光后只启一个
3. config.yaml 缺模型 — 补 model 字段
