# 云服务器部署清单

将 Hermes + API 中转站完整迁移到阿里云 ECS 的步骤记录。

## 环境

- 阿里云 ECS，Ubuntu 24.04 LTS
- 1核2G，40GB 云盘
- 实例名：`iZ2vc1r6idxmchd2xcvb18Z`
- 公网 IP：按实际分配

## 部署步骤

### 1. 服务器基础加固

```bash
# Swap（防 OOM）
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# pip 镜像（国内必需）
pip3 config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 安装 python3.12 + pipx
sudo apt update && sudo apt install python3.12 python3.12-venv pipx -y
```

### 2. 迁移 Hermes

```bash
# 本机：打包
hermes backup -o ~/hermes-migration.zip

# scp 到服务器
scp ~/hermes-migration.zip admin@<IP>:/home/admin/

# 服务器：还原
pipx install hermes-agent
hermes import /home/admin/hermes-migration.zip --force

# 或直接用 venv 安装
python3 -m venv ~/hermes_env
~/hermes_env/bin/pip install hermes-agent
~/hermes_env/bin/hermes import /home/admin/hermes-migration.zip --force
```

### 3. .env 密钥

确保 `~/.hermes/.env` 包含：
```
DEEPSEEK_API_KEY=sk-xxx
DASHSCOPE_API_KEY=sk-xxx
SILICONFLOW_API_KEY=sk-xxx
SENSENOVA_API_KEY=sk-xxx
QQ_APP_ID=xxx
QQ_CLIENT_SECRET=xxx
```

### 4. PATH 设置

```bash
sudo ln -sf ~/hermes_env/bin/hermes /usr/local/bin/hermes
```

### 5. systemd 保活

```bash
# 开 linger（允许未登录时运行用户服务）
sudo loginctl enable-linger $USER

# 网关服务
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/hermes-gateway.service << 'EOF'
[Unit]
Description=Hermes Agent Gateway
After=network-online.target
[Service]
Type=simple
ExecStart=%h/hermes_env/bin/hermes gateway run --replace
Restart=always
RestartSec=10
[Install]
WantedBy=default.target
EOF

# 中转站服务
cat > ~/.config/systemd/user/api-relay.service << 'EOF'
[Unit]
Description=API Relay Server
After=network-online.target
[Service]
Type=simple
WorkingDirectory=%h/api-relay
EnvironmentFile=%h/.hermes/.env
ExecStart=%h/hermes_env/bin/python %h/api-relay/server.py
Restart=always
RestartSec=5
[Install]
WantedBy=default.target
EOF

export XDG_RUNTIME_DIR=/run/user/$(id -u)
systemctl --user daemon-reload
systemctl --user enable --now hermes-gateway api-relay
```

注意：每次执行 `systemctl --user` 前如果报 "Failed to connect to bus"，需要先 `export XDG_RUNTIME_DIR=/run/user/$(id -u)`。

### 6. 阿里云安全组

进入 ECS 控制台 → 安全组 → 入方向 → 添加规则：

| 端口 | 协议 | 来源 | 用途 |
|------|------|------|------|
| 22 | TCP | 0.0.0.0/0 | SSH |
| 8848 | TCP | 0.0.0.0/0 | API 中转站 |

### 7. 验证

```bash
hermes status                    # QQ + 微信在线？
curl 127.0.0.1:8848/health       # 中转站 ok？
curl <公网IP>:8848/health        # 外网可达？
```

### 8. 定时任务

```bash
# 每日备份：0 4 * * *
# Galgame 速报：0 9 * * *
# 服务器播报：0 8,20 * * *
# 中转站监控：*/5 * * * *
```

## 常见问题

| 问题 | 解决 |
|------|------|
| pip 超时 | 配阿里云镜像 |
| pip 拒绝安装 | 装到 hermes_env venv 里 |
| 8848 外网不通 | 改 host 为 0.0.0.0 + 开安全组 |
| systemctl --user 不通 | export XDG_RUNTIME_DIR |
| 端口被占 | fuser -k 8848/tcp |
| Chromium not found | apt install chromium-browser（走 snap，慢） |
| ripgrep not found | apt install ripgrep |
