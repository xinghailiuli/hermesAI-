# Cron 健康检查模板

## 正确模式：使用 check_relay.py 脚本

**推荐方式**（自动探测端口，仅异常时报告）：

```bash
# 在 cron prompt 中：
python3 ~/.hermes/skills/infra/api-relay/scripts/check_relay.py
# exit 0 → 健康，输出 "HEALTHY | port=..."
# exit 1 → 异常，输出 "FAILED | port=..." 或 "NO_RELAY_FOUND"
```

结合 [SILENT] 交付模式 — cron 任务应检查 exit code：
- exit 0 → 返回 `[SILENT]` 不打扰用户
- exit 1 → 直接报告异常信息给用户

## 错误模式：硬编码端口 8848 ❌

```
curl -s 127.0.0.1:8848/health
```

问题：
- 实际 Flask relay 可能运行在 8847（当 Codex WS Bridge 部署后）
- `Connection refused` 可能是正常状态（WS 桥没运行），不是故障
- 导致误报或漏报

## Cron 执行中的自动恢复策略

当 cron prompt 中硬编码了 `curl 127.0.0.1:8848/health`（常见于旧 cron 任务），agent 在 cron 执行期应**自动兜底**而非直接报错：

1. **先按 prompt 的端口检查**：`curl 127.0.0.1:8848/health`
2. **如果 Connection refused**：不急于报错，先查实际端口
3. **探测实际端口**：`ss -tlnp | grep python.*server\.py` → 提取 LISTEN 端口
4. **用实际端口重试健康检查**
5. **仅在实际端口也无响应时才报异常**

Cron prompt 示例（带自动兜底逻辑）：

```
检查API中转站健康。先试 curl -s --max-time 10 http://127.0.0.1:8848/health，如果返回非ok，查询实际运行端口 ss -tlnp | grep python.*server.py，用实际端口重试。仅当所有端口都无响应才报告异常；正常则[SILENT]。
```

这样即使旧 cron prompt 写死了 8848，agent 也能自行发现正确的 8847 并正确判定服务健康，无需人为更新 cron 配置。

## 调试步骤（异常时）

当健康检查失败时：

1. **确认 Flask relay 实际运行端口**
   ```
   ss -tlnp | awk '/python.*server\\.py/ {split($4,a,":"); print a[2]}' | head -1
   ```

2. **确认进程存活且工作正常**
   ```
   RELAY_PORT=$(ss -tlnp | awk '/python.*server\\.py/ {split($4,a,":"); print a[2]}')
   curl -s --max-time 10 "http://127.0.0.1:${RELAY_PORT}/health"
   ```

3. **检查 systemd 服务状态**
   ```
   systemctl --user status api-relay
   ```

4. **查看重启计数（判断是否在无限循环）**
   ```
   systemctl --user show api-relay -p NRestarts
   ```

5. **查看日志中的端口冲突**
   ```
   journalctl --user -u api-relay -n 50 --no-pager | grep -E "Address already in use|Port.*in use"
   ```

## 典型场景处理

| 场景 | `ss -tlnp :PORT` | `curl :PORT/health` | 处理方式 |
|------|-----------------|-------------------|---------|
| 正常服务 | 8847 有监听 | `{"status":"ok"}` | 无需操作 |
| systemd 循环但旧进程正常 | 8847 有监听（PID ≠ systemd 最新） | `{"status":"ok"}` | `systemctl --user stop api-relay`（保留旧进程） |
| 进程死但端口僵尸 | 8847 无监听，但 `lsof -i :8847` 有 PID | `Connection refused` | `kill -9 $(lsof -ti :8847)` + 重启 |
| 完全挂了 | 无监听 | `Connection refused` | 重新启动中转站 |
