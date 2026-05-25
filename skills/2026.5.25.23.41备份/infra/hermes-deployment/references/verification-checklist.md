# 部署后验证清单

SSH 到目标服务器后逐项执行。每个 `✓` 都是必须过的。

## 1. 基础健康检查

```bash
hermes --version           # 确认安装成功
hermes doctor              # 完整诊断（API 连通性、工具可用性）
hermes config show         # 检查模型提供商和 API key
```

关键指标：
- Python 环境 ✓
- 配置文件存在 ✓
- API key 已配置 ✓
- 模型提供商连通 ✓（至少一个）

## 2. 网关进程

```bash
ps aux | grep hermes | grep -v grep
```

确认 gateway run 进程存在。如果是在 tmux/screen 里跑的，注意重启后会丢——建议配 systemd。

## 3. 监听端口

```bash
ss -tlnp | grep -E 'hermes|python'
```

常见端口：
- 8848: API 中转站（如果有）
- 9119: Dashboard Web UI（如果有）
- 8080: Gateway HTTP（如果配置了）

## 4. 网关日志

```bash
tail -50 ~/.hermes/logs/gateway.log
```

确认：
- 无 crash/error 反复出现
- 频道连接日志正常（QQ Bot / WeChat / Telegram 等 inbound message 出现）
- 响应时间正常（`response ready` 有合理 time=N.Ns）

## 5. 频道连通性

在日志中搜索各平台 inbound 消息确认频道在线：
```bash
grep "inbound message" ~/.hermes/logs/gateway.log | tail -10
```

预期看到各平台有消息流入。

## 6. systemd 持久化（推荐）

如果还没配，现在就配（见 SKILL.md systemd 部分）。配完后：
```bash
sudo systemctl status hermes-gateway
sudo systemctl enable hermes-gateway   # 确保开机自启
```

## 常见问题速查

| 症状 | 排查方向 |
|------|---------|
| gateway 进程不在 | tmux 断了 → 重开或配 systemd |
| 频道无 inbound | 检查 auth.json / session 文件是否过期 |
| API 调用失败 | `.env` 的 key 是否正确，能否出网 |
| 端口不通 | 阿里云安全组 / 防火墙规则 |
