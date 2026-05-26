# GitHub 备份同步

将 Hermes 备份同步到 GitHub 私有仓库。备份仓库路径：`~/hermesAI-backup`。

## 仓库结构

```
~/hermesAI-backup/
├── hermes agent/
│   └── YYYY.M.D.HH.MM备份/     ← hermes backup zip 放这里
├── skills/
│   └── YYYY.M.D.HH.MM备份/     ← ~/.hermes/skills/ 快照
├── 中转站/
│   └── YYYY.M.D.HH.MM备份/     ← api-relay 文件快照
└── 阿罗娜角色/
    └── YYYY.M.D.HH.MM备份/     ← 角色配置快照
```

## 同步流程

```bash
BACKUP_DIR=~/hermesAI-backup
TIMESTAMP=$(date +%Y.%m.%d.%H.%M)

# 1. Hermes 备份 zip 复制到仓库
cp /home/admin/hermes-backups/hermes-$(date +%Y%m%d).zip \
   "$BACKUP_DIR/hermes agent/$TIMESTAMP备份/hermes.zip"

# 2. Skills 快照
cp -r ~/.hermes/skills/ "$BACKUP_DIR/skills/$TIMESTAMP备份/"

# 3. 中转站快照
cp -r ~/api-relay/ "$BACKUP_DIR/中转站/$TIMESTAMP备份/"

# 4. 提交推送
cd "$BACKUP_DIR"
git add -A
git commit -m "$TIMESTAMP 备份"
git push
```

## GitHub 认证

仓库使用 HTTPS + token 认证：

```bash
git remote set-url origin "https://xinghailiuli:${GH_TOKEN}@github.com/xinghailiuli/hermesAI-.git"
```

### Token 过期处理

GitHub 不再支持密码认证，需要 Personal Access Token (classic)：
1. 去 github.com/settings/tokens/new 生成
2. 勾选 `repo` 权限
3. `export GH_TOKEN=<新token>` 或更新 remote URL

Token 过期时 git push 报错：`Invalid username or token. Password authentication is not supported for Git operations.`

## 清理旧备份

```bash
# 保留最近 7 个 zip
ls -t /home/admin/hermes-backups/hermes-*.zip | tail -n +8 | xargs rm -v
```
