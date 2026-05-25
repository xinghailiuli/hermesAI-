# GitHub 每日备份

将 Hermes 配置 + API 中转站每日备份到 GitHub 仓库，按日期分文件夹。

## 仓库结构

```
hermesAI-/
├── hermes/
│   ├── 2026-05-25/    ← config、skills、cron、memory、systemd 服务文件
│   └── 2026-05-26/
├── 中转站/
│   ├── 2026-05-25/    ← API 中转站全部代码
│   └── 2026-05-26/
```

## 首次设置

```bash
# 1. 克隆备份仓库（token 放 URL 里避免交互）
git clone "https://USERNAME:TOKEN@github.com/USER/REPO.git" /home/admin/backup-repo-name
cd /home/admin/backup-repo-name

# 2. 初始化目录结构
mkdir -p hermes 中转站
rm -f 旧占位文件
git add -A && git commit -m "init" && git push

# 3. 配置 git 身份（用于 cron 自动提交）
git config user.email "bot@example.com"
git config user.name "Backup Bot"
```

**⚠️ Token 权限要求**：至少需要 `repo` scope（读写仓库）。Fine-grained token 选择 "Contents: Read and write"。

## 备份脚本

```bash
#!/bin/bash
# 每日自动备份到 GitHub
set -e

REPO_DIR="/home/admin/hermesAI-backup"
DATE=$(date +%Y-%m-%d)
GH_TOKEN=$(cat /home/admin/.hermes/gh_token)

cd "$REPO_DIR"
git pull origin main -q 2>/dev/null

# Hermes 备份
mkdir -p "hermes/${DATE}"
cp -r /home/admin/.hermes/config.yaml \
      /home/admin/.hermes/skills/ \
      /home/admin/.hermes/cron/ \
      /home/admin/.hermes/memory* \
      "hermes/${DATE}/" 2>/dev/null || true

# systemd 服务文件备份
mkdir -p "hermes/${DATE}/systemd"
cp /etc/systemd/system/api-relay.service \
   /etc/systemd/system/mihomo.service \
   "hermes/${DATE}/systemd/" 2>/dev/null || true

# 中转站备份
mkdir -p "中转站/${DATE}"
cp -r /home/admin/api-relay/* "中转站/${DATE}/" 2>/dev/null || true

# 推送
git add -A
git commit -m "📦 每日备份 ${DATE}" || { echo "无变更，跳过"; exit 0; }
git push "https://USERNAME:${GH_TOKEN}@github.com/USER/REPO.git" main
echo "✅ 备份完成 ${DATE}"
```

## 配置 cron 每日执行

```bash
# 每天凌晨 3 点执行
0 3 * * * /home/admin/scripts/daily-backup-github.sh >> /tmp/backup-github.log 2>&1
```

## Pitfalls

### Token URL 编码
`ghp_` 开头的 classic token 直接放 URL 没问题。Fine-grained token 含特殊字符需 URL 编码，或存文件用 `cat` 读取。

### 免交互推送
`git push` 的 URL 直接嵌 token（`https://USER:TOKEN@github.com/...`）避免 SSH key 管理和 passphrase 交互。
