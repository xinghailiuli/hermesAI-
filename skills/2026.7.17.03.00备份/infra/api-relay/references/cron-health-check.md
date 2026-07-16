# Cron 健康检查模板

## 正确模式：使用 check_relay.py 脚本

**推荐方式**（自动探测端口，仅异常时报告）：

```bash
python3 ~/.hermes/skills/infra/api-relay/scripts/check_relay.py
```

exit code 0=健康 → cron agent 返回 `[SILENT]`
exit code 1=异常 → 报告异常信息

## 错误模式：硬编码端口 8848 ❌

```
curl -s 127.0.0.1:8848/health
```

问题：
- 实际 Flask relay 可能运行在 8847（当 Codex WS Bridge 部署后）
- `Connection refused` 可能是正常状态（WS 桥没运行），不是故障
- 导致误报或漏报

## Agent 自动兜底模式（推荐 cron prompt 写法）

当 cron prompt 中硬编码了 `curl 127.0.0.1:8848/health`（常见于旧 cron 任务），agent 在 cron 执行期应**自动兜底**而非直接报错：

1. **先按 prompt 的端口检查**：`curl 127.0.0.1:8848/health`
2. **如果 Connection refused**：不急于报错，先查实际端口
3. **探测实际端口**：`ss -tlnp | grep 8847` 或 `ss -tlnp | grep python` 提取 LISTEN 端口
4. **用实际端口重试健康检查**
5. **仅在实际端口也无响应时才报异常**；正常则 `[SILENT]`

> ⚠️ `ss -tlnp` 输出中的进程名可能是 `python3` 而不是 `server.py`。搜索 "server.py" 会漏匹配，应搜索 "python" + 端口号（8847/8848）组合。

Cron prompt 示例（带自动兜底逻辑）：

```markdown
检查API中转站健康。先试 curl -s --max-time 10 http://127.0.0.1:8848/health，
如果返回非ok，查询实际运行端口 ss -tlnp | grep python，提取 LISTEN 端口号重试。
仅当所有端口都无响应才报告异常；正常则[SILENT]。
```

这样即使旧 cron prompt 写死了 8848，agent 也能自行发现正确的 8847 并正确判定服务健康。

## 调试步骤（异常时）

当健康检查失败时：

1. **确认 Flask relay 实际运行端口**
   ```bash
   ss -tlnp | awk '/python/ && /:88[14][78]/ {split($4,a,":"); print a[2]}' | head -1
   ```

2. **确认进程存活且工作正常**
   ```bash
   RELAY_PORT=$(ss -tlnp | awk '/python/ && /:88[14][78]/ {split($4,a,":"); print a[2]}')
   curl -s --max-time 10 "http://127.0.0.1:${RELAY_PORT}/health"
   ```

3. **检查 systemd 服务状态**
   ```bash
   systemctl --user status api-relay
   ```

4. **查看重启计数（判断是否在无限循环）**
   ```bash
   systemctl --user show api-relay -p NRestarts
   ```

5. **查看日志中的端口冲突**
   ```bash
   journalctl --user -u api-relay -n 50 --no-pager | grep -E "Address already in use|Port.*in use"
   ```

## 典型场景处理

| 场景 | `ss -tlnp :PORT` | `curl :PORT/health` | 处理方式 |
|------|-----------------|-------------------|---------|
| 正常服务 | 8847 有监听 | `{"status":"ok"}` | 无需操作 |
| systemd 循环但旧进程正常 | 8847 有监听（PID ≠ systemd 最新） | `{"status":"ok"}` | `systemctl --user stop api-relay`（保留旧进程） |
| 进程死但端口僵尸 | 8847 无监听，但 `lsof -i :8847` 有 PID | `Connection refused` | `kill -9 $(lsof -ti :8847)` + 重启 |
| 完全挂了 | 无监听 | `Connection refused` | 重新启动中转站 |
