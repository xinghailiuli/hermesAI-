# 双开冲突恢复流程

## 背景

Hermes 迁移到云服务器后，如果本地 WSL 的实例没有停止，会出现两个实例同时连接微信/QQ 的情况。

## 症状

- 用户发一条消息，回复来源不稳定（有时本地回、有时云端回）
- 定时任务（cron）同一时间推送两次
- `hostname` 显示为本地机器名而非服务器 hostname
- 用户关掉本地 WSL 后 Hermes "掉线"（因为刚才回复的是本地实例）

### 网关日志特征

两台实例抢同一个 QQ/微信连接时，日志会频繁出现：

```
Shutdown phase: all adapters disconnected at +0.00s
✓ weixin connected
[QQBot] WebSocket connected → Connected
✓ qqbot connected
```

在短时间内（几分钟）反复出现上述日志 = 双开互踢。正常运行应该稳定数小时不会重连。

```bash
# 快速诊断
grep -c "Connected account" ~/.hermes/logs/gateway.log
# 如果一天几十次连接记录 = 双开冲突
```

## 恢复步骤

### 1. 确认当前在跟哪个实例说话

```bash
hostname
```

### 2. 停掉本地网关

```bash
systemctl --user stop hermes-gateway
systemctl --user disable hermes-gateway  # 阻止下次开机自启
```

或直接 kill 进程：
```bash
pkill -f "hermes gateway run"
```

> ⚠️ `pkill` 可能被系统超时拦截（返回 `BLOCKED: Command timed out`），此时改用：
> ```bash
> kill $(pgrep -f "hermes gateway run")
> # 或
> systemctl --user stop hermes-gateway
> ```

### 3. 验证云端接管

发一条微信消息 → 云端实例应该回复。如果云端回复了，说明接管成功。

### 4. 清理云端重复 cron

云端接管后，让它自检 cron：
```bash
hermes cron list
```

如果本地和云端有重复的 cron job（同名/同时间），云端只需要保留自己那套。用 `hermes cron remove <job_id>` 清理多余项。

### 5. （可选）恢复本地访问云端

如果本地没有 SSH 密钥，无法直接管理云端。需要通过以下方式之一：

- **微信间接管理**：云端已接管微信，通过微信给云端下指令
- **阿里云控制台 VNC**：通过网页终端直接登录服务器
- **sshpass 密码登录**（需要安装 `sshpass`）：
  ```bash
  # 安装
  sudo apt install sshpass -y
  
  # 使用（密码会短暂出现在进程列表，用完建议清理 bash history）
  sshpass -p '你的密码' ssh -o StrictHostKeyChecking=no admin@<IP> "hostname"
  
  # 如需交互式会话
  sshpass -p '你的密码' ssh -o StrictHostKeyChecking=no admin@<IP>
  ```

## 预防

迁移完成后立即执行：
```bash
# 在本地
systemctl --user stop hermes-gateway
systemctl --user disable hermes-gateway
```

并验证云端正常工作后再关掉本地终端。
