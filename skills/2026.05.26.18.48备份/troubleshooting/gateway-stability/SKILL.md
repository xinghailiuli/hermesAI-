---
name: gateway-stability
description: Hermes Gateway 频繁掉线/被杀/重启的诊断与修复。不适用于 WSL 网络问题。
---

# 网关稳定性诊断

## 一、快速定因（按顺序排查）

网关被 systemd 报 `status=9/KILL` 或频繁重启时，**不要直接假定是 OOM/内存不足**。按以下顺序排查：

### 0. 检查 systemd 是否在主动杀网关（最关键！）

```bash
journalctl --user -u hermes-gateway.service --since "10 min ago" | grep 'Stopping hermes-gateway'
```

如果看到 `systemd[PID]: Stopping hermes-gateway.service`，说明 **systemd 自己决定停服务**，不是网关自己崩的。常见原因：
- **`--replace` 标志自残**：`ExecStart` 带了 `--replace`，新实例检测到旧实例后触发 systemd 停止循环
- **hermes.service（root 级）冲突**：`systemctl status hermes.service` 检查是否有另一个 hermes 服务在跑

**修复**：
```bash
# 1. 删掉 --replace
sed -i 's/gateway run --replace/gateway run/' /home/admin/.config/systemd/user/hermes-gateway.service

# 2. 停掉冲突的 root 级服务
sudo systemctl stop hermes.service
sudo systemctl disable hermes.service

# 3. 重载
systemctl --user daemon-reload
systemctl --user restart hermes-gateway.service
```

### 0b. 如果 systemd 无论如何都杀网关 → 切 tmux

当 systemd 持续发 SIGTERM/SIGKILL 且以上修复无效时，**放弃 systemd，改用 tmux + watchdog**：

```bash
# 禁用 systemd 服务
systemctl --user disable --now hermes-gateway.service
systemctl --user mask hermes-gateway.service

# 创建 watchdog 脚本
cat > /home/admin/hermes-gw-watchdog.sh << 'WDOG'
#!/bin/bash
SESSION="hermes-gw"
while true; do
    if ! tmux has-session -t "$SESSION" 2>/dev/null; then
        tmux new-session -d -s "$SESSION" \
            "cd /home/admin && /home/admin/hermes_env/bin/python -m hermes_cli.main gateway run 2>&1 | tee -a /tmp/hermes-gw.log"
        echo "$(date): Gateway started" >> /tmp/hermes-gw-watchdog.log
    fi
    sleep 30
done
WDOG

chmod +x /home/admin/hermes-gw-watchdog.sh

# 启动 watchdog（重启后自动启动）
(crontab -l 2>/dev/null; echo '@reboot sleep 10 && tmux new-session -d -s hermes-watchdog "/home/admin/hermes-gw-watchdog.sh"') | crontab -

# 立即启动
tmux new-session -d -s hermes-watchdog '/home/admin/hermes-gw-watchdog.sh'
```

> ⚠️ 注意：阿里云网页终端（`hermes` CLI on ttyS0）会与网关冲突，打开终端后记得 `exit` 退出。

### 1. 检查平台限流
```bash
journalctl --user -u hermes-gateway.service --since "10 min ago" | grep -i 'rate.limit'
```
**微信平台极易触发限流**，限流后退避重试会导致网关崩溃 → systemd 发 SIGKILL。
修复：注释掉 `.env` 中对应平台的配置行，重启网关。

### 2. 检查是否有多个 Hermes 实例冲突
```bash
ps aux | grep -i hermes | grep -v grep
```
典型冲突场景：
- 阿里云网页终端开着 `hermes` CLI（ttyS0），与 systemd 网关互殴
- tmux 里残留旧网关实例
- 两个 systemd user 实例

systemd 检测到冲突会发 SIGTERM，网关不响应则补 SIGKILL。
修复：`kill <冲突PID>` 清理非网关的 Hermes 进程。

### 3. 检查真实 OOM（最后才怀疑这个）
```bash
dmesg | grep -i 'oom\|killed' | tail -10        # 内核 OOM 记录
free -h                                           # 系统内存
systemctl --user status hermes-gateway.service | grep Memory  # cgroup 内存
```
- 网关进程内存峰值 > 1.2G 且 dmesg 有 OOM 记录 → 真内存不足
- 网关只有 100-200M 且 dmesg 无 OOM → 不是内存问题，回到步骤 1 或 2

## 二、内存优化（仅在真 OOM 时执行）

以下优化对 1.6G 内存服务器有效，但如果根因不是内存则完全无效：

```bash
# 错开 cron 高峰
hermes config set cron.max_parallel_jobs 1

# 减少会话轮数
hermes config set agent.max_turns 30

# 关闭上下文压缩
hermes config set compression.enabled false

# 清理无用系统服务
sudo systemctl disable --now ModemManager multipathd tuned udisks2 unattended-upgrades

# 激进 swap
sudo sysctl -w vm.swappiness=100
```

systemd 服务文件内存限制：
```ini
MemoryHigh=1.1G
MemoryMax=1.5G
MemorySwapMax=0
```

## 三、每次被杀必定检查项

| 检查 | 命令 |
|------|------|
| 被杀前最后日志 | `journalctl --user -u hermes-gateway.service --since "5 min ago" \| tail -20` |
| 平台连接状态 | `cat ~/.hermes/gateway_state.json \| python3 -m json.tool` |
| 是否有重复进程 | `ps aux \| grep hermes \| grep -v grep` |

## 四、常见伪根因（不要被骗）

- ❌ "内存不足" — 网关实际只用 100-200M，系统内存使用 < 50% 时不是内存问题
- ❌ "cron 任务太多" — max_parallel_jobs=1 的前提下，cron 不会同时跑
- ❌ "swap 不够" — swap 几乎不用，swappiness=100 也没用
- ❌ "OOM Killer 杀的" — 先检查 `dmesg | grep oom`，没有记录就不是 OOM
- ✅ **微信限流** — 最常见真凶
- ✅ **进程冲突** — 阿里云网页终端 / tmux 残留
- ✅ **systemd + --replace 自残** — systemd 主动停服务，不是网关崩了
- ✅ **hermes.service（root 级）冲突** — 与 user 级 gateway 打架
- ✅ **SSL 解密失败** — DeepSeek API 偶发证书/连接问题导致网关崩溃，通常自动恢复无需人工干预

## 五、QQ Bot WebSocket 超时（无害）

日志中每 30 分钟出现一次属于正常现象：

```
WARNING gateway.platforms.qqbot.adapter: [QQBot:1904043129] WebSocket closed: code=4009 reason=Session timed out
```

这是 QQ Bot 平台自身的会话超时机制（30 分钟无活动断开），网关会自动重连，**无需处理**。只有在连续多次重连失败后才需要关注。

## 六、重新启用已禁用的平台（微信等）

平台被禁用（env vars 被注释）后重新启用的步骤：

### 6.1 取消注释 .env 变量
```bash
sed -i 's/^#WEIXIN_/WEIXIN_/' /home/admin/.hermes/.env
```

### 6.2 确保 config.yaml 有平台段
如果 `config.yaml` 中完全没有 `weixin:` 段（即使在 .env 设了变量也不会加载该平台）：
```yaml
# config.yaml 中需要有其一段（哪怕空对象）
weixin: {}
```
缺少此段 = 网关不初始化该平台 adapter。

### 6.3 重启网关（注意：正在连接的会话会阻塞 drain）
```bash
sudo systemctl restart hermes-gateway
```
如果 `restart` 超时：当前活跃的 agent 会话（包括你自己正在聊天的 SSH 连接）会阻塞旧进程的 drain（drain_timeout 默认 180s）。等待最多 3.5 分钟（TimeoutStopSec 210s），systemd 会强行 SIGKILL 旧进程然后启动新实例。此时连接会中断一下，属于正常现象。

### 6.4 验证平台上线
```bash
# 检查平台是否在可发送列表
send_message action=list  # 通过 agent 调用

# 或检查日志
journalctl -u hermes-gateway --since "2min ago" | grep -i weixin
```
发送一条测试消息确认收发正常。
