---
name: hermes-restore
description: 从 GitHub 备份仓库恢复 Hermes 配置、技能、定时任务和角色设定
category: infra
---

# Hermes 从 GitHub 备份恢复

从 GitHub 备份仓库 (`xinghailiuli/hermesAI-`) 恢复 Hermes Agent 的完整状态。

## 触发条件

- 部署了新环境需要恢复配置
- Hermes 数据丢失需要从备份还原
- 老师要求「用 GitHub 备份恢复记忆」
- 跨机器迁移后需要恢复技能和定时任务

## 备份仓库结构

```
hermesAI-/
├── hermes agent/           # Hermes 主配置备份
│   └── <时间戳>备份/
│       ├── config.yaml     # 完整 Hermes 配置
│       ├── SOUL.md         # 角色灵魂文件
│       └── jobs.json       # 定时任务导出
├── 阿罗娜角色/             # 阿罗娜角色配置
│   └── <时间戳>备份/
│       ├── config.yaml     # personality: kawaii
│       ├── SOUL.md         # 默认 Hermes 提示
│       └── auth.json       # 认证凭据池
├── skills/                 # 技能备份
│   └── <时间戳>备份/
│       └── infra/          # 按类别组织
│           └── <skill-name>/SKILL.md
├── 中转站/                 # API 中转站备份
│   └── <时间戳>备份/
│       ├── server.py
│       ├── config.json
│       └── dashboard.html
└── 表情包/                 # 表情包图片
```

## 恢复步骤

### 1. 设置 GitHub 认证

```bash
# 方式一：credential helper（推荐，无需安装 gh CLI）
git config --global credential.helper 'store --file ~/.git-credentials'
echo "https://<username>:<token>@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials

# 方式二：安装 GitHub CLI
# curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
# echo "deb ... https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list
# sudo apt-get update && sudo apt-get install -y gh
```

### 2. 定位并克隆备份仓库

```bash
# 方式一：SSH（推荐 — 避免 Git GnuTLS 代理兼容问题）
git clone git@github.com:<user>/<repo>.git /tmp/hermes-restore/

# 方式二：HTTPS + Token（需要 credential helper 或嵌入 URL）
git clone https://<username>:<token>@github.com/<user>/<repo>.git /tmp/hermes-restore/
```

> **注意：** 若服务器使用 mihomo 代理，git HTTPS 可能因 GnuTLS 与代理节点不兼容而失败（`gnutls_handshake() failed`）。此时请使用 SSH 方式，并配置 `core.sshCommand` 走 SOCKS5 代理。详见 `server-proxy-mihomo` 技能的「Git GnuTLS Pitfall」章节。

### 3. 恢复技能

```bash
# 取最新时间戳备份（按文件名排序取最后一个）
BACKUP=$(ls -d /tmp/hermes-restore/<repo>/skills/*备份/ | sort | tail -1)
mkdir -p ~/.hermes/skills/infra
cp -r "$BACKUP"infra/* ~/.hermes/skills/infra/
```

### 4. 恢复定时任务

从 `jobs.json` 读取每个 job，用 `cronjob(action='create', ...)` 逐个重建。关键字段映射：

| jobs.json 字段 | cronjob 参数 |
|---------------|-------------|
| `name` | `name` |
| `prompt` | `prompt` |
| `schedule.expr` | `schedule` |
| `deliver` | `deliver` |
| `enabled_toolsets` | `enabled_toolsets` |

注意：`deliver: "local"` 仅保存不推送；`deliver: "origin"` 推送到当前对话。

### 5. 恢复角色配置

```bash
mkdir -p ~/.hermes/characters

# 普拉娜（主角色，personality: plana）
cp "<repo>/hermes agent/<最新>备份/SOUL.md" ~/.hermes/characters/plana-soul.md
cp "<repo>/hermes agent/<最新>备份/config.yaml" ~/.hermes/characters/plana-config.yaml

# 阿罗娜（personality: kawaii）
cp "<repo>/阿罗娜角色/<最新>备份/SOUL.md" ~/.hermes/characters/arona-soul.md
cp "<repo>/阿罗娜角色/<最新>备份/config.yaml" ~/.hermes/characters/arona-config.yaml
```

### 6. 保存关键记忆到持久存储

用 `memory` 工具保存从备份中提取的关键事实：
- GitHub 用户名、Token 状态
- LLM 提供者配置（DeepSeek main, SiliconFlow fallback）
- 角色设定
- 插件列表

**不要保存**：具体的 job ID、PR 号、commit SHA、任务进度等会快速过时的信息。

### 7. 清理

```bash
rm -rf /tmp/hermes-restore
```

## 验证清单

- [ ] `ls ~/.hermes/skills/infra/` 有技能目录
- [ ] `cronjob(action='list')` 列出所有定时任务且 enabled=true
- [ ] `ls ~/.hermes/characters/` 有 arona-* 和 plana-* 文件
- [ ] memory 中有 GitHub 和提供者信息

## 参考

- `references/jobs-json-format.md` — cron job JSON 导出格式详解
- GitHub token 配置脚本：来自 `cloud-proxy-setup` 技能的 `references/github-token-setup.md`
- 角色切换技能：`character-switch`
- 备份系统：`hermes-backup` 技能 — 备份脚本位置、GnuTLS 兼容性修复、SSH+SOCKS5 代理配置
