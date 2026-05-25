---
name: hermes-cloud-deploy
description: 将 Hermes Agent 从本机迁移到云服务器，实现 24/7 在线运行。包含备份、SCP 传输、安装、还原、systemd 保活的完整流程。
---

# Hermes 云服务器部署

把 Hermes 从本地 WSL/电脑迁移到云服务器，电脑关机也能用。

## 适用场景

- 买了阿里云/腾讯云轻量服务器，想把 Hermes 搬上去
- 本地电脑不能 24 小时开机
- 从一台机器迁移到另一台

---

## 第一步：本机打包

```bash
hermes backup -o ~/hermes-migration.zip
```

输出示例：55MB 原始 → ~14MB 压缩包。包含 config.yaml、state.db（记忆/会话）、skills、auth、.env、cron 等全部状态。

---

## 第二步：传到服务器

```bash
scp ~/hermes-migration.zip root@<服务器IP>:/root/
```

---

## 第三步：服务器安装 Hermes

### 标准方式（pipx）

```bash
sudo apt update && sudo apt install python3.12 python3.12-venv pipx -y
pipx ensurepath
pipx install hermes-agent
```

### ⚠️ 国内服务器 pipx 常见问题

#### 问题 1：pip 下载慢/连不上

```bash
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

或每次带 `-i` 参数：

```bash
pipx install hermes-agent --pip-args="-i https://pypi.tuna.tsinghua.edu.cn/simple"
```

#### 问题 2：「upgrading shared libraries」卡很久

这是 pipx 在本地编译依赖（特别是 llama-index 全家桶和 C 扩展）。**阿里云轻量 1 核 1G 可能需要 10-20 分钟**，不是卡死。

⚠️ **不要换回官方源！** 这步是在编译，跟网络无关。换回官方源可能反而连不上。

#### 问题 3：内存不够 OOM

低配服务器（≤1G 内存）编译时可能被杀进程。尝试：

```bash
# 限制并行编译
pipx install hermes-agent --pip-args="--no-build-isolation"
```

#### 终极兜底：跳过 pipx，直接 pip

如果 pipx 实在跑不动：

```bash
python3 -m venv ~/hermes-venv
~/hermes-venv/bin/pip install hermes-agent -i https://pypi.tuna.tsinghua.edu.cn/simple
ln -s ~/hermes-venv/bin/hermes ~/.local/bin/hermes
```

更快，少一层隔离开销。

---

## 第四步：还原备份

```bash
hermes import /root/hermes-migration.zip --force
```

验证：

```bash
hermes --version
hermes doctor
```

---

## 第五步：systemd 保活

创建 `/etc/systemd/system/hermes-gateway.service`：

```ini
[Unit]
Description=Hermes Gateway
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=root
ExecStart=/root/.local/bin/hermes gateway run
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启用自启：

```bash
systemctl daemon-reload
systemctl enable --now hermes-gateway
systemctl status hermes-gateway
```

---

## 重要提醒

| 事项 | 说明 |
|------|------|
| **⚠️ 关掉本地实例** | 迁移后务必停掉本地的 Hermes 网关！否则本地和云端同时在线，微信/QQ 消息被争抢，cron 任务双倍执行。详见 `hermes-cloud-migration` 技能的 `references/dual-instance-recovery.md` |
| **QQ Bot IP** | 迁移后服务器 IP 变了，检查 QQ Bot 平台是否绑定了 IP 白名单 |
| **微信通道** | 可能需重新扫码授权 |
| **API Key** | backup 带了 .env，但建议手动确认一遍 |
| **api-relay 中转站** | 也可一起搬到服务器，配 systemd 双保活 |

---

## 参考：api-relay 服务也搬上去

```bash
scp -r ~/api-relay root@<IP>:/root/
```

服务器上：

```bash
cd /root/api-relay
export $(grep -v '^#' /root/.hermes/.env | xargs)
nohup python3 server.py > /tmp/api-relay.log 2>&1 &
```

配 systemd 略（同理）。
