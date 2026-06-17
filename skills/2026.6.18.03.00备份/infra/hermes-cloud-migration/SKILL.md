---
name: hermes-cloud-migration
description: Migrate Hermes Agent from a local machine to a cloud server for 24/7 uptime. Covers backup, server setup, restore, systemd, and co-deployment with API relay.
---

# Hermes 云服务器迁移

将 Hermes Agent 从本地（WSL/Windows/macOS）迁移到云服务器，实现 24/7 在线运行。

## 适用场景

- 本地电脑关机后仍需要 Hermes 响应消息（QQ/微信等）
- 需要 API 中转站 24 小时在线
- 从 WSL2 迁移到云服务器

## 前置条件

- 一台 Linux 云服务器（推荐 Ubuntu 22.04/24.04，1核2G 以上）
- 本机 Hermes v0.14+ 已配置好频道（QQBot/微信等）
- SSH 可连服务器

## 步骤一：本机备份

```bash
hermes backup -o ~/hermes-migration.zip
```

这会打包 `~/.hermes/` 下的配置、状态数据库、技能、记忆、频道绑定、API 密钥。排除 Hermes 代码本体。

## 步骤二：传输到服务器

```bash
scp ~/hermes-migration.zip admin@你的服务器IP:/home/admin/
```

## 步骤三：服务器初始化

### 3.1 确认 Python 环境

```bash
python3.12 --version  # Ubuntu 24.04 默认 3.12
sudo apt install python3.12-venv -y
```

### 3.2 创建 venv 并安装 Hermes

```bash
python3.12 -m venv ~/hermes_env
~/hermes_env/bin/pip install hermes-agent
```

**国内服务器注意**：先配 pip 镜像源（阿里云），否则安装超时：
```bash
pip3 config set global.index-url https://mirrors.aliyun.com/pypi/simple/
```

### 3.3 还原备份

```bash
~/hermes_env/bin/hermes import ~/hermes-migration.zip --force
```

### 3.4 加到 PATH

```bash
sudo ln -sf /home/admin/hermes_env/bin/hermes /usr/local/bin/hermes
```

### 3.5 验证

```bash
hermes status
```

确认 DeepSeek API Key 存在、QQBot 和微信频道已配置。

## 步骤四：配置 systemd 保活

### 4.1 开启 lingering

```bash
sudo loginctl enable-linger admin
```

### 4.2 创建 Hermes Gateway 服务

```bash
mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/hermes-gateway.service << 'EOF'
[Unit]
Description=Hermes Gateway
After=network-online.target

[Service]
Type=simple
ExecStart=/home/admin/hermes_env/bin/hermes gateway run
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now hermes-gateway
```

### 4.3 检查

```bash
systemctl --user status hermes-gateway
hermes status
```

## 步骤五：添加 Swap（低配服务器必备）

1.6G 内存无 swap 会导致 OOM 被杀。添加 2G swap：

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### 步骤六：部署 API 中转站

迁移完成后中转站不会自动部署。参阅 `api-relay` 技能的「从零重建中转站」小节。

**安装 Flask 依赖**（Ubuntu 24.04 + pipx 环境）：

pipx 的 venv 不含 pip，不能用 `~/hermes_env/bin/pip`。改用系统 Python + proxy：

```bash
# 必须走代理，否则 pip 超时
export HTTP_PROXY=http://127.0.0.1:7897 HTTPS_PROXY=http://127.0.0.1:7897
pip3 install flask requests --break-system-packages
```

**创建 systemd 服务**（使用系统 python3 + EnvironmentFile 注入密钥和代理）：
cat > ~/.config/systemd/user/api-relay.service << 'EOF'
[Unit]
Description=API Relay Server
After=network-online.target

[Service]
Type=simple
WorkingDirectory=%h/api-relay
EnvironmentFile=%h/.hermes/.env
Environment=HTTP_PROXY=http://127.0.0.1:7897
Environment=HTTPS_PROXY=http://127.0.0.1:7897
Environment=http_proxy=http://127.0.0.1:7897
Environment=https_proxy=http://127.0.0.1:7897
Environment=NO_PROXY=localhost,127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,.local,.internal
ExecStart=/usr/bin/python3 %h/api-relay/server.py
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now api-relay
```

## 验证清单

> 📋 完整恢复流程见 `references/post-reset-recovery.md`
> 🛠️ 编码终端工具安装见 `server-proxy-mihomo` 技能的 `references/deepseek-coding-tools.md`

### ⚠️ gh_token 生存检查（迁移后必做！）

`~/.hermes/gh_token` 在 `hermes backup` 备份范围内（`~/.hermes/` 目录），但迁移还原后**可能丢失**（文件权限、符号链接、部分还原失败）。迁移后第一条命令验证：

```bash
# 检查文件存在且内容非空
[ -s ~/.hermes/gh_token ] && echo "✓ gh_token 存在 ($(wc -c < ~/.hermes/gh_token) bytes)" || echo "❌ gh_token 丢失"

# 验证 token 有效
TOKEN=$(cat ~/.hermes/gh_token 2>/dev/null)
curl -s -H "Authorization: Bearer $TOKEN" -x http://127.0.0.1:7897 https://api.github.com/user | python3 -c "import sys,json; d=json.load(sys.stdin); print('用户:', d.get('login','❌'), '|', d.get('message','OK'))"
# → 用户: xinghailiuli | OK
```

**如果丢失**：用户需重新提供 Personal Access Token（GitHub → Settings → Developer settings → Tokens）。收到后存入：

```bash
echo "github_pat_..." > ~/.hermes/gh_token && chmod 600 ~/.hermes/gh_token
```

```bash
# Hermes 网关
systemctl --user status hermes-gateway
hermes status | grep -E "Status|QQBot|Weixin"

# API 中转站
systemctl --user status api-relay
curl http://127.0.0.1:8848/health
curl http://127.0.0.1:8848/v1/chat/completions \
  -H 'Authorization: Bearer sk-local-apirelay-2026' \
  -H 'Content-Type: application/json' \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"hi"}],"max_tokens":20}'
```

## Pitfalls

### ⚠️ `hermes backup` 不备份 `~/api-relay/` 和自定义工具（最重要！）

`hermes backup` 只打包 `~/.hermes/` 下的内容（配置、记忆、技能、会话、频道绑定）。**以下目录不会被备份**：

| 不会被备份 | 影响 |
|---|---|
| `~/api-relay/` | 中转站代码全丢，需从零重建 |
| `~/gh_tools.py`、`~/cgc` 等 | 自定义工具脚本丢失 |
| `~/api-relay-backups/` | 中转站历史备份丢失 |
| `/etc/mihomo/config.yaml` | 代理配置丢失（需重配） |

**迁移 checklist**：
```bash
# 备份 hermes 数据
hermes backup -o ~/hermes-migration.zip

# 备份中转站
tar czf ~/api-relay-backup.tar.gz ~/api-relay/

# 备份代理配置
sudo cp /etc/mihomo/config.yaml ~/mihomo-config-backup.yaml

# 全部传到新服务器
scp ~/hermes-migration.zip ~/api-relay-backup.tar.gz ~/mihomo-config-backup.yaml admin@新IP:~/
```

### ⚠️ 本地实例未关闭 → 双开冲突（最常见问题）

迁移到云端后，如果**本地 Hermes 没有停止**，会导致：

| 问题 | 表现 |
|------|------|
| 消息抢占 | 微信/QQ 消息被两个实例争抢，回复不稳定 |
| Cron 双倍执行 | 所有定时任务执行两次，用户收到重复推送 |
| 记忆/技能分叉 | 两边各自累积不同的记忆和技能，越用越乱 |

**诊断你是否在跟本地还是云端说话**：

```bash
hostname   # 本地 WSL 通常是用户机器名，云端是服务器 hostname
```

**修复步骤**：

1. 停掉本地网关：`systemctl --user stop hermes-gateway`（或 kill 进程）
2. 发一条微信消息 → 云端实例接管
3. 在云端检查并清理重复的 cron：`hermes cron list`
4. 移除本地的 systemd 自启（如果配了）：`systemctl --user disable hermes-gateway`

**预防**：迁移完成后，务必在本地执行 `systemctl --user stop hermes-gateway` 并 disable 自启。

### SSH 密钥丢失

迁移后本地 `.ssh/` 可能没有私钥，导致无法 SSH 回云端管理。如果云端已接管微信，可通过微信让云端自检和修复。参考 `references/dual-instance-recovery.md`。

### 频道绑定失效
迁移后 QQBot/微信可能因 IP 变化需要重新验证。QQBot 检查 AppID/ClientSecret 是否绑定了 IP 白名单；微信通道可能需要重新扫码。`hermes status` 确认平台状态为 `connected`。

### pipx vs venv 混淆
不要混用 pipx 和手动 venv。本流程统一用 `~/hermes_env/` venv。如果已有 pipx 安装的 Hermes，`pipx uninstall hermes-agent` 清理后再按本流程操作。

### 内存不足
1.6G 服务器无 swap 时 Hermes + Python 可能 OOM。务必添加 swap（步骤五）。DeepSeek 推理请求本身不占本机内存——OOM 来源是 Hermes 进程本身（~500MB）+ Python venv + 系统开销。

### 安全组 / 防火墙
如果要从外部访问中转站 dashboard：
- 修改 `config.json` 的 `server.host` 为 `0.0.0.0`
- 云服务商安全组开放 8848 端口
- 或通过 Nginx 反代 + SSL 暴露

**建议**：中转站只监听 `127.0.0.1`，通过 Hermes 网关间接调用，避免暴露公网端口。

### ⚠️ hermes backup 不包含 api-relay（数据丢失高危）

`hermes backup` 只打包 `~/.hermes/` 目录（配置、记忆、技能、会话、频道绑定）。**它不会备份 `~/api-relay/` 目录**。服务器重置/迁移后，中转站的所有源文件（server.py、config.json、dashboard.html）会丢失。

**预防**：
- 迁移前务必单独备份 `~/api-relay/`：`tar czf ~/api-relay-backup.tar.gz ~/api-relay/`
- 或使用 cron 定时任务每日备份中转站（见下方示例）
- 将 api-relay 核心文件保存为 `api-relay` 技能的模板（`templates/`），方便重建

**恢复**：如果 api-relay 文件已丢失，可：
1. 从 `api-relay` 技能的 `templates/` 复制 server.py / config.json / dashboard.html
2. 调整 config.json 中的模型列表
3. 创建 systemd 服务并启动

### 代理环境变量（systemd drop-in）

云端 hermese-gateway 服务需要代理才能访问 GitHub 等外网。通过 systemd drop-in 注入环境变量：

```bash
mkdir -p ~/.config/systemd/user/hermes-gateway.service.d
cat > ~/.config/systemd/user/hermes-gateway.service.d/proxy.conf << 'EOF'
[Service]
Environment="HTTP_PROXY=http://127.0.0.1:7897"
Environment="HTTPS_PROXY=http://127.0.0.1:7897"
Environment="http_proxy=http://127.0.0.1:7897"
Environment="https_proxy=http://127.0.0.1:7897"
Environment="NO_PROXY=localhost,127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,.local,.internal"
EOF
systemctl --user daemon-reload
systemctl --user restart hermes-gateway
```
