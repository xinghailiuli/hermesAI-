---
name: hermes-deployment
description: Deploy, migrate, backup, and restore Hermes Agent across machines and cloud servers.
---

# Hermes 部署、备份与恢复

将 Hermes 从一个环境搬到另一个环境（本机→云服务器、重装系统后恢复等），以及每日 GitHub 备份和灾难恢复。

## 迁移流程

### 步骤 1：源机器打包

```bash
# 完整备份（配置 + 记忆 + 技能 + 会话 + 频道绑定 + 密钥）
hermes backup -o ~/hermes-migration.zip

# 快速备份（仅关键文件：config、state.db、.env、auth、cron）
hermes backup --quick -o ~/hermes-quick.zip
```

备份包含：config.yaml、state.db（记忆/会话）、skills/、.env、auth.json、channel_directory.json、cron/、memories/

备选恢复路径：如果本地 `hermes-backups/` 目录丢失但 GitHub 备份仓库 `xinghailiuli/hermesAI-` 中有备份，可从 GitHub 直接恢复。详见 `references/github-backup-restore.md`。

### 步骤 2：目标机器安装 Hermes

```bash
# Ubuntu/Debian
sudo apt update && sudo apt install python3.12 python3.12-venv pipx -y
pipx ensurepath && exec $SHELL
pipx install hermes-agent

# 验证
hermes --version
```

### 步骤 3：传输并还原

```bash
# 从源机器 scp 过去
# scp ~/hermes-migration.zip user@server:/home/user/

# 目标机器上还原
hermes import /home/user/hermes-migration.zip --force
```

### 步骤 4：验证

```bash
hermes doctor          # 检查配置完整性
hermes config list     # 确认模型和 provider
cat ~/.hermes/.env     # 确认 API 密钥正确
```

### 步骤 5：启动网关

```bash
hermes gateway run
```

---

## 云服务器持久运行（systemd）

迁移到云服务器后，配 systemd 服务确保重启自动拉起：

```bash
sudo tee /etc/systemd/system/hermes-gateway.service << 'EOF'
[Unit]
Description=Hermes Agent Gateway
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
ExecStart=/root/.local/bin/hermes gateway run
Restart=always
RestartSec=15
Environment=HOME=/root

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now hermes-gateway

# 检查
sudo systemctl status hermes-gateway
```

---

## 备份（GitHub 每日备份）

将 Hermes 配置、技能、角色和中转站每日自动备份到 GitHub 私有仓库。

### 备份脚本

脚本位置：`~/.hermes/scripts/github-daily-backup.py`
Cron job：每日凌晨 3:00，`no_agent` 模式直接运行脚本。

### 备份内容

四类文件夹全量快照，每日推送：

```
hermesAI-/
├── hermes agent/       ← config.yaml + characters/
├── skills/             ← ~/.hermes/skills/ (全量)
├── 中转站/              ← /home/admin/api-relay/ (config.json, server.py, dashboard.html)
└── 阿罗娜角色/          ← character SOUL.md + config.yaml
```

时间戳格式：`YYYY.M.D.HH.MM备份`（月日不补零，时分补零）。

### 手动触发

```bash
python3 ~/.hermes/scripts/github-daily-backup.py
```

### 关键 Pitfalls

| Pitfall | 症状 | 解决 |
|---------|------|------|
| Git GnuTLS + mihomo 代理不兼容 | `gnutls_handshake() failed: The TLS connection was non-properly terminated.` | 使用 SSH 协议 + SOCKS5 代理（`GIT_SSH_COMMAND` 设置 `ProxyCommand nc -X 5 -x 127.0.0.1:7897`） |
| SSH Key 未配置 | push 失败 | 添加 Deploy Key 或用户级 SSH Key 到 GitHub |
| hermes CLI 在 cron 中不可用 | `command not found` | 使用完整路径 `~/.local/bin/hermes` 或用 curl + GitHub API 验证 |
| 本地 zip 旧备份堆积 | `~/hermes-backups/` 无限增长 | 清理逻辑必须在 `no_agent` 模式运行（agent 模式的 `rm` 会被安全审批拦截） |

详细排查和配置见 `references/daily-backup-pitfalls.md` 和 `references/github-backup-sync.md`。

### 本地 Zip 备份

除 GitHub 远程备份外，系统还有本地 zip 快照：`~/hermes-backups/hermes-YYYYMMDD.zip`（每天约 10-12 MB）。与 GitHub 备份互为冗余，互不依赖。

---

## 恢复（从 GitHub 备份还原）

从 GitHub 备份仓库 `xinghailiuli/hermesAI-` 恢复 Hermes 完整状态。

### 快速恢复流程

```bash
# 1. 设置 GitHub 认证
git config --global credential.helper 'store --file ~/.git-credentials'
echo "https://<user>:<token>@github.com" > ~/.git-credentials && chmod 600 ~/.git-credentials

# 2. 克隆备份仓库（SSH 推荐，避免 GnuTLS 问题）
git clone git@github.com:xinghailiuli/hermesAI-.git /tmp/hermes-restore/

# 3. 恢复技能
LATEST=$(ls -d /tmp/hermes-restore/skills/*备份/ | sort | tail -1)
mkdir -p ~/.hermes/skills/infra && cp -r "$LATEST"infra/* ~/.hermes/skills/infra/

# 4. 恢复角色配置
cp "hermes agent/"*备份/SOUL.md ~/.hermes/characters/plana-soul.md
cp "阿罗娜角色/"*备份/SOUL.md ~/.hermes/characters/arona-soul.md

# 5. 从 jobs.json 重建 cron 任务（用 cronjob create 工具，不用 CLI）
# 6. 保存关键信息到 memory
# 7. 清理：rm -rf /tmp/hermes-restore/
```

完整步骤和验证清单见 `references/github-backup-restore.md`。jobs.json 字段映射见 `references/jobs-json-format.md`。

---

## 频道重新认证风险

| 频道 | 风险 |
|------|------|
| **QQ Bot** | IP 变化后 QQ 开放平台可能标记异常；检查是否配置了 IP 白名单 |
| **微信 Bot** | 可能需要重新扫码授权；weixin/accounts/ 下的 session 文件迁移后通常可用 |
| **Telegram** | 重新运行 `hermes telegram` 即可重绑 |

---

## Pitfalls

### 恢复后网关不自动连接频道
备份包含 channel_directory.json 和 auth.json，但某些 OAuth token 可能过期。`hermes gateway run` 后观察日志：
```bash
tail -f ~/.hermes/logs/gateway.log
```
看到平台 state 变为 `connected` 即为成功。

### API 密钥不一致
源机器的 .env 和环境变量与目标机器隔离。还原后务必检查 `~/.hermes/.env` 内容是否正确。如果源机器用了系统级环境变量（非 .env 文件），需要在目标机器上手动设置。

### pipx PATH 未生效
云服务器上装完 pipx 后 `hermes` 命令找不到：
```bash
pipx ensurepath
exec $SHELL
# 或直接 export PATH="$HOME/.local/bin:$PATH"
```

### Cron `deliver: "origin"` 跨平台陷阱

`origin` 解析到 cron 创建时的平台，切换平台后不会跟随。详见 `references/cron-management.md`。

### 插件安装后未备份

安装新插件后必须备份到 GitHub。用户要求**所有备份（四类：hermes agent + skills + 中转站 + 阿罗娜角色）都必须同步到 GitHub**，不能只备份 Hermes zip。详见 `references/plugin-management.md` 和 `references/github-backup-sync.md`。

### GitHub 备份脚本更新后

修改 `~/.hermes/scripts/github-daily-backup.py` 后务必测试运行一次，确保能正常 clone、commit、push。Cron job 是 `no_agent=true` 模式，脚本错误不会有 LLM 兜底。

### 时间戳格式

备份文件夹时间戳格式为 `YYYY.M.D.HH.MM备份`（月日不补零，时分补零）。Python 使用 `%Y.%-m.%-d.%H.%M`，注意 `%-H`/`%-M` 会去掉前导零导致格式错乱（如 `23.3` 应为 `23.03`）。

### GitHub Token 过期

备份同步到 GitHub 时 token 过期导致 push 失败。**立刻报告用户，不要沉默切换方案。**
解决：生成 Classic token 选「No expiration」永久有效，或配 SSH key 一劳永逸。
详见 `references/github-backup-sync.md`。
