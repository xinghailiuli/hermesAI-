# GitHub 备份同步

将 Hermes 所有备份增量同步到 GitHub 私有仓库 `xinghailiuli/hermesAI-`。
**自动化脚本**：`~/.hermes/scripts/github-daily-backup.py`（cron 每日 3:00 自动运行，no_agent 模式）。

> **用户要求**：增量备份（只推当天变动的文件），不重复塞整个目录。按仓库现有文件夹结构管理，命名格式保持一致。不删除旧存档。

## 仓库结构（四类文件夹，表情包不参与备份）

```
xinghailiuli/hermesAI-/
├── hermes agent/                    ← ~/.hermes/config.yaml + characters/
│   └── YYYY.M.D.HH.MM备份/
├── skills/                          ← ~/.hermes/skills/
│   └── YYYY.M.D.HH.MM备份/
├── 中转站/                          ← /home/admin/api-relay/
│   └── YYYY.M.D.HH.MM备份/
│       ├── config.json
│       ├── server.py
│       ├── dashboard.html
│       └── requirements.txt
├── 阿罗娜角色/                      ← ~/.hermes/characters/ 角色文件
│   └── YYYY.M.D.HH.MM备份/
│       ├── arona-soul.md / plana-soul.md
│       └── arona-config.yaml / plana-config.yaml
└── 表情包/                          ← 不参与备份
    └── *.png / *.gif
```

## 时间戳格式

**严格按照 `YYYY.M.D.HH.MM备份` 格式**。Python: `datetime.now().strftime("%Y.%-m.%-d.%H.%M备份")`。
- 月/日不补零：`5` 而非 `05`
- 时/分补零：`09` 而非 `9`、`03` 而非 `3`
- 示例：`2026.5.27.23.55备份`

## 增量备份逻辑

脚本每次运行时：

1. **clone/pull** 仓库到 `/tmp/hermes-backup-repo`
2. **对比上一份备份**：找到每个类别文件夹下时间戳最新的子目录作为基准
3. **只复制变动的文件**：用 SHA256 hash 比对，跳过未改动的文件
4. **git add -A && git commit && git push**
5. **清理临时目录**
6. **无变动则跳过**：如果所有文件都没变，不产生提交，直接退出
7. **首次运行自动全量**：没有历史备份时，所有文件视为新增

## 自动化备份脚本

脚本位置：`~/.hermes/scripts/github-daily-backup.py`

核心映射：

```python
FOLDERS = {
    "hermes agent": {
        "~/.hermes/config.yaml": "config.yaml",
        "~/.hermes/characters": "characters",
    },
    "skills": {
        "~/.hermes/skills": ".",
    },
    "中转站": {
        "/home/admin/api-relay/config.json": "config.json",
        "/home/admin/api-relay/server.py": "server.py",
        "/home/admin/api-relay/dashboard.html": "dashboard.html",
        "/home/admin/api-relay/requirements.txt": "requirements.txt",
    },
    "阿罗娜角色": {
        "~/.hermes/characters/arona-soul.md": "arona-soul.md",
        "~/.hermes/characters/plana-soul.md": "plana-soul.md",
        "~/.hermes/characters/arona-config.yaml": "arona-config.yaml",
        "~/.hermes/characters/plana-config.yaml": "plana-config.yaml",
    },
}
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

## 旧备份管理

不自动清理。用户明确要求「不删除旧存档」，所有历史备份永久保留在 GitHub 上。GitHub 仓库空间充足，无需担心。
