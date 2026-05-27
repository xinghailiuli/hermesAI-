# GitHub 备份同步

将 Hermes 所有备份同步到 GitHub 私有仓库 `xinghailiuli/hermesAI-`。
本地路径：`~/hermesAI-backup`。

> **用户要求**：所有备份都要和 GitHub 同步，不只是 Hermes zip。四类备份一个不能少。

## 仓库结构（四类文件夹）

```
~/hermesAI-backup/
├── hermes agent/
│   └── YYYY.M.D.HH.MM备份/
│       ├── hermes-YYYYMMDD.zip     ← hermes backup 完整 zip
│       ├── config.yaml              ← Hermes 配置
│       └── mihomo.service           ← 代理服务文件
├── skills/
│   └── YYYY.M.D.HH.MM备份/         ← ~/.hermes/skills/ 完整快照
├── 中转站/
│   └── YYYY.M.D.HH.MM备份/         ← ~/api-relay/ 完整快照
│       ├── server.py
│       ├── config.json
│       ├── dashboard.html
│       └── requirements.txt
└── 阿罗娜角色/
    └── YYYY.M.D.HH.MM备份/
        ├── SOUL.md                  ← 角色定义
        └── config.yaml              ← 角色配置
        ⚠️ 不备份 auth.json！  ← 含 API 密钥，绝对不能上传 GitHub
```

## 完整同步脚本

```bash
BACKUP_DIR=~/hermesAI-backup
TS="$(date +%Y.%-m.%-d.%-H.%-M)备份"  # 无前导零：2026.5.26.16.30备份

mkdir -p "$BACKUP_DIR/hermes agent/$TS" \
         "$BACKUP_DIR/skills/$TS" \
         "$BACKUP_DIR/中转站/$TS" \
         "$BACKUP_DIR/阿罗娜角色/$TS"

# 1. Hermes agent: zip + 关键配置文件
cp /home/admin/hermes-backups/hermes-$(date +%Y%m%d).zip "hermes agent/$TS/"
cp ~/.hermes/config.yaml "hermes agent/$TS/" 2>/dev/null
cp /etc/systemd/system/mihomo.service "hermes agent/$TS/" 2>/dev/null

# 2. Skills 完整快照
cp -r ~/.hermes/skills/ "skills/$TS/"

# 3. 中转站完整快照
cp -r ~/api-relay/ "中转站/$TS/"

# 4. 阿罗娜角色（不含 auth.json！）
cp ~/.hermes/SOUL.md "阿罗娜角色/$TS/" 2>/dev/null
cp ~/.hermes/config.yaml "阿罗娜角色/$TS/" 2>/dev/null
# ⚠️ 绝对不要 cp ~/.hermes/auth.json！

# 5. 提交推送
cd "$BACKUP_DIR"
git add -A
git commit -m "📦 全量备份 $TS"
git push
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
# 方式1：直接更新 remote URL
cd ~/hermesAI-backup
git remote set-url origin "https://xinghailiuli:新TOKEN@github.com/xinghailiuli/hermesAI-.git"
git push

# 方式2：用环境变量
export GH_TOKEN="新TOKEN"
git remote set-url origin "https://xinghailiuli:${GH_TOKEN}@github.com/xinghailiuli/hermesAI-.git"
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

## 大文件推送超时

Hermes 备份 zip 可达 85MB+，`git push` 默认 60s 超时不够。
用后台模式 + `notify_on_complete`：

```bash
# 不要直接用 git push（会超时）
# 用 background=true + notify_on_complete=true
terminal(command="cd ~/hermesAI-backup && git push", background=true, notify_on_complete=true, timeout=300)
```

## Git LFS 大文件管理

Hermes 备份 zip 可达 85MB+，超过 GitHub 建议上限 50MB（硬上限 100MB）。长期累积会被警告甚至拒绝。

### 一次性配置

```bash
# 1. 安装 Git LFS
sudo apt-get install -y git-lfs

# 2. 初始化并追踪 zip 文件
cd ~/hermesAI-backup
git lfs install
git lfs track "*.zip"
git add .gitattributes
git commit -m "🔧 启用 Git LFS 支持大文件备份"

# 3. 迁移已有 zip 到 LFS（会重写 git 历史，需 force push）
git lfs migrate import --include="*.zip" --everything
git push --force
```

迁移完成后，zip 文件在仓库中只占指针（~130 bytes），实际文件存在 LFS 存储。之后再 `git push` 不受 50MB 限制。

### Git LFS 迁移注意事项

- `git lfs migrate import --everything` 会**重写全部历史**，之后必须 `git push --force`
- 迁移过程可能耗时较长，用 background 模式执行
- 只在首次配置时需要 migrate；之后的新 zip 自动走 LFS

## 清理旧备份

```bash
# 保留最近 7 个 zip
ls -t /home/admin/hermes-backups/hermes-*.zip | tail -n +8 | xargs rm -v
```
