# QQ Bot Session Timeout — 这是正常的

部署 Hermes 到云服务器后，QQ Bot 每隔 **30 分钟** 会自动断开重连。这是 QQ 官方 API 的限制，不是 Bug。

## 日志特征

```
WARNING gateway.platforms.qqbot.adapter: [QQBot:xxx] WebSocket closed: code=4009 reason=Session timed out
INFO gateway.platforms.qqbot.adapter: [QQBot:xxx] Reconnecting in 2s (attempt 1)...
INFO gateway.platforms.qqbot.adapter: [QQBot:xxx] WebSocket connected to wss://api.sgroup.qq.com/websocket
INFO gateway.platforms.qqbot.adapter: [QQBot:xxx] Ready, session_id=xxx
```

## 确认 Bot 在线的方法

```bash
# 查看最近 5 条 QQ 相关日志
grep -i "qq" ~/.hermes/logs/gateway.log | tail -5

# 如果最后一条是 "Ready" 且时间在 30 分钟内 → 在线
# 如果最后一条是 "Session timed out" 且没有后续 "Ready" → 可能在重连中（等 5 秒再查）
```

## 预期行为

- 断开：每 30 分钟一次（code 4009）
- 重连时间：2-5 秒
- 用户无感知：短暂间隙通常不会丢消息
- Token 刷新：access token 也会定期刷新（约 6000 秒过期）

## "灵魂不在线"：Ready 但消息不响应

这是比 timeout 更隐蔽的故障模式 — 日志显示 `Ready`、WebSocket 已连接，但 Bot 完全不回消息。

**根因**：网关主循环被重复错误刷屏阻塞（如 sqlite3 数据库损坏、插件异常等），虽然 WebSocket 层保持连接，但消息分发线程已卡死。

**诊断**：
```bash
# 看日志尾部，排除正常的 timeout 重连噪音
tail -30 ~/.hermes/logs/gateway.log | grep -v "Session timed out\|Reconnecting\|kanban"
# 如果每分钟都有一条同样的错误 → 主循环被阻塞
```

**快速修复**（以 kanban.db 损坏为例）：
```bash
rm -f ~/.hermes/kanban.db*
kill $(cat ~/.hermes/gateway.pid)
hermes gateway run
```

## 什么时候需要人工介入

- 连续 3 次以上 `Reconnecting` 失败（attempt 3+ 仍未 Ready）
- 出现 `401` 或 `403` 错误（密钥/权限问题，不是 timeout）
- 日志中出现 `Connection refused` 而非 `Session timed out`
- **"Ready" 但消息不响应** → 见上方"灵魂不在线"
