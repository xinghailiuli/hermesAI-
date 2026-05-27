# GitHub 备份同步

将 Hermes 所有备份同步到 GitHub 私有仓库 `xinghailiuli/hermesAI-`。
**自动化脚本**：`~/.hermes/scripts/github-daily-backup.py`（cron 每日 3:00 自动运行，no_agent 模式）。

> **用户要求**：所有备份都要和 GitHub 同步，不只是 Hermes zip。按仓库现有文件夹结构管理。

## 仓库结构（五类文件夹）

```
xinghailiuli/hermesAI-/
├── hermes agent/
│   └── YYYY.M.D.HH.MM备份/
│       ├── config.yaml              ← ~/.hermes/config.yaml
│       └── characters/              ← ~/.hermes/characters/ 完整目录
├── skills/
│   └── YYYY.M.D.HH.MM备份/         ← ~/.hermes/skills/ 完整快照
├── 中转站/
│   └── YYYY.M.D.HH.MM备份/
│       ├── config.json
│       ├── server.py
│       ├── dashboard.html
│       └── requirements.txt
├── 阿罗娜角色/
│   └── YYYY.M.D.HH.MM备份/
│       ├── arona-soul.md
│       ├── arona-config.yaml
│       ├── plana-soul.md
│       └── plana-config.yaml
└── 表情包/
    └── *.png / *.gif               ← 不参与备份，手动管理
```

## 自动化备份脚本

脚本位置：`~/.hermes/scripts/github-daily-backup.py`

```python
#!/usr/bin/env python3
"""Daily Hermes backup to GitHub — no_agent cron job."""
# 核心逻辑：
# 1. clone/pull 仓库到 /tmp/hermes-backup-repo
# 2. 按 SRC_MAP 定义的映射，将本地文件复制到 YYYY.M.D.HH.MM备份/ 子目录
# 3. 每类保留最近 KEEP=7 份，旧备份自动清理
# 4. git add -A && git commit && git push
# 5. 清理临时目录
```

Cron 配置：`no_agent=true, script="github-daily-backup.py", schedule="0 3 * * *"`

### 手动触发

```bash
python3 ~/.hermes/scripts/github-daily-backup.py
```

## GitHub Token 管理

### 为什么老过期

GitHub 不再支持密码认证，只用 token。两种 token 类型：

| 类型 | 过期 | 推荐 |
|------|------|------|
| Fine-grained | 最长 1 年，必过期 | ❌ |
| Classic | 可选「No expiration」永不过期 | ✅ |

**一次性解决**：生成 Classic token 时选 **No expiration** + 勾 `repo`。

生成地址：https://github.com/settings/tokens/new

### Token 过期时怎么办

过期症状：`git push` 报 `Invalid username or token. Password authentication is not supported for Git operations.`

**不要沉默切换方案！立刻告诉用户 token 过期了。**

更新方式：

```bash
# 更新 git credential store
echo "https://xinghailiuli:新TOKEN@github.com" > ~/.git-credentials
chmod 600 ~/.git-credentials

# 验证
cd /tmp && git clone https://github.com/xinghailiuli/hermesAI-.git
```

### 长期方案：SSH Key（推荐）

配 SSH key 后彻底告别 token 过期问题：

```bash
# 生成密钥（如已有则跳过）
ssh-keygen -t ed25519 -C "admin@hermes" -f ~/.ssh/github_hermes

# 添加公钥到 GitHub: https://github.com/settings/keys
cat ~/.ssh/github_hermes.pub

# 切换 remote 为 SSH
cd ~/hermesAI-backup
git remote set-url origin git@github.com:xinghailiuli/hermesAI-.git
```

## Git LFS 大文件管理

Hermes 备份 zip 可达 85MB+，超过 GitHub 建议上限 50MB（硬上限 100MB）。

仓库已配置 Git LFS（`.gitattributes` 中 `*.zip filter=lfs`），新 zip 自动走 LFS。

## 清理旧备份

脚本自动处理（`prune_old` 函数），无需手动干预。每类保留最近 7 份。
