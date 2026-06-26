# Server Health Check — 完整参考

## 检查项和命令

### 系统资源

```bash
# 磁盘使用率
df -h /

# 内存
free -h

# CPU 负载
uptime
# 建议：1min 负载 ≤ 核心数×2 为健康
nproc  # 查看核心数
```

### 服务状态

**API 中继 (api-relay)**
```bash
curl -s -o /dev/null -w "%{http_code}" --max-time 5 127.0.0.1:8848/health
```

**Hermes Gateway**
```bash
hermes gateway status
# 或
systemctl --user status hermes-gateway
```

**Mihomo 代理**
```bash
systemctl --user status mihomo
ss -tlnp | grep 7897
```

## Pitfalls

### Gateway 无 HTTP health 端点
Gateway 不暴露 TCP health 端点 — 它只对外连接到消息平台和 LLM API。不要尝试 `curl http://127.0.0.1:18080/health`，这不存在。使用 `hermes gateway status` CLI 命令。

### Gateway 日志中的 API 错误不是服务器故障
网关可能显示 SSL 错误（`WRONG_VERSION_NUMBER`）、流中断、`RemoteProtocolError`。这些是 upstream LLM API 通过代理通信时的正常重试行为。仅在以下情况标记异常：
- 服务不是 `active (running)`
- 持续全部重试失败（检查日志时间戳）
- 内存使用 > 2GB 持续增长

### Mihomo bind error
即使 `systemctl --user status mihomo` 显示 startup `bind: address already in use` 错误，端口仍可能正在监听。用 `ss -tlnp | grep 7897` 二次确认。

## 报告格式

```
# 一切正常
今日服务器播报：良好

# 发现问题
今日服务器播报：[具体问题描述]

# 无需报告（cron silent mode）
[SILENT]
```
