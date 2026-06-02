# GitHub 每日增量备份

将 Hermes Agent 配置 + Skills + 阿罗娜角色 + API 中转站每日备份到 GitHub 仓库，按时间戳分文件夹。使用增量备份（rsync --ignore-existing），仅备份当天变动文件。

## 仓库结构

```
hermesAI-/
├── 阿罗娜角色/              ← SOUL.md + auth.json + config.yaml
│   └── 2026.5.26.3.0备份/
├── skills/                  ← 全部 Skills 独立备份
│   └── 2026.5.26.3.0备份/
├── hermes agent/            ← 核心配置 + cron jobs + systemd 服务
│   └── 2026.5.26.3.0备份/
└── 中转站/                  ← API 中转站全部代码
    └── 2026.5.26.3.0备份/
```

时间戳格式：`YYYY.M.D.HH.MM备份`（如 `2026.5.25.23.33备份`）。四个文件夹齐平，各管各的。

## 首次设置

```bash
# 1. 克隆备份仓库（token 放 URL 里避免交互）
git clone "https://USERNAME:TOKEN@github.com/USER/hermesAI-.git" /home/admin/hermesAI-backup
cd /home/admin/hermesAI-backup

# 2. 配置 git 身份（用于 cron 自动提交）
git config user.email "arona@hermes.ai"
git config user.name "Arona"

# 3. 安装 git（备份脚本依赖）
sudo apt install -y git
```

**⚠️ Token 权限要求**：至少需要 `repo` scope（读写仓库）。如需 Star 收藏仓库则额外需要 `public_repo` scope。

## 备份脚本

脚本路径：`/home/admin/scripts/daily-backup-github.sh`

核心设计：
- **全量备份**：每次运行都完整复制源文件（`cp -r`），每天的快照自包含、可独立恢复
- 四类独立目录：阿罗娜角色、Skills、Hermes Agent 核心配置、中转站
- 时间戳精确到分钟：`YYYY.M.D.HH.MM备份`
- Git 自动去重：相同文件不产生新 blob（git 层优化），但目录结构完整

> ⚠️ **为什么是全量而非增量**：增量备份看似节省空间，但每天的快照不完整——恢复时需要拼接所有增量。用户明确要求每天备份自包含、可独立恢复。

```bash
#!/bin/bash
# 每日全量备份到 GitHub — 每天快照自包含、可独立恢复
set -e

REPO_DIR="/home/admin/hermesAI-backup"
TIMESTAMP=$(date +%Y.%-m.%-d.%-H.%-M)
GH_TOKEN=$(cat /home/admin/.hermes/gh_token)

cd "$REPO_DIR"
git pull origin main -q 2>/dev/null

echo "📦 全量备份 ${TIMESTAMP}"

# ─── 阿罗娜角色 ───
D="阿罗娜角色/${TIMESTAMP}备份"
mkdir -p "$D"
cp /home/admin/.hermes/SOUL.md     "$D/" 2>/dev/null || true
cp /home/admin/.hermes/auth.json   "$D/" 2>/dev/null || true
cp /home/admin/.hermes/config.yaml "$D/" 2>/dev/null || true
echo "  ✅ 阿罗娜角色"

# ─── Skills ───
D="skills/${TIMESTAMP}备份"
mkdir -p "$D"
cp -r /home/admin/.hermes/skills/* "$D/" 2>/dev/null || true
echo "  ✅ Skills"

# ─── Hermes Agent ───
D="hermes agent/${TIMESTAMP}备份"
mkdir -p "$D"
cp /home/admin/.hermes/config.yaml       "$D/" 2>/dev/null || true
cp /home/admin/.hermes/cron/jobs.json     "$D/" 2>/dev/null || true
cp /home/admin/.hermes/memory*            "$D/" 2>/dev/null || true
cp /etc/systemd/system/api-relay.service  "$D/" 2>/dev/null || true
cp /etc/systemd/system/mihomo.service     "$D/" 2>/dev/null || true
echo "=== $(date) ===" > "$D/已安装工具.txt"
ls -lh /usr/local/bin/{claude,deepseek,codewhale,codewhale-tui} 2>/dev/null >> "$D/已安装工具.txt"
echo "  ✅ Hermes Agent"

# ─── 中转站 ───
D="中转站/${TIMESTAMP}备份"
mkdir -p "$D"
cp -r /home/admin/api-relay/* "$D/" 2>/dev/null || true
echo "  ✅ 中转站"

# ─── 推送 ───
git add -A
git commit -m "📦 全量备份 ${TIMESTAMP}" || { echo "无变更"; exit 0; }
git push "https://xinghailiuli:${GH_TOKEN}@github.com/xinghailiuli/hermesAI-.git" main 2>&1
echo "✅ 全量备份完成！"

## 配置 cron 每日执行

```bash
# 每天凌晨 3 点执行
0 3 * * * /home/admin/scripts/daily-backup-github.sh >> /tmp/backup-github.log 2>&1
```

## Pitfalls

### Token URL 编码
`ghp_` 开头的 classic token 直接放 URL 没问题。Fine-grained token 含特殊字符需 URL 编码，或存文件用 `cat` 读取。

### Token 存储位置
存于 `~/.hermes/gh_token`，脚本通过 `cat` 读取避免泄露在命令行历史中。

### Token 权限范围
- `repo` scope：仅用于 git push/pull（备份够用）
- `public_repo` scope：额外允许 Star 收藏仓库
- **Fine-grained PAT**：需在 GitHub 设置中单独勾选 **「Starring: Read and write」** 才能 star 仓库。经典 PAT (classic) 勾 `public_repo` 即可，Fine-grained PAT 用独立权限模型，默认不包含 Starring。

### 防止备份垃圾文件（关键！）
**不要 `cp -r .hermes/*`** 全量复制！运行时数据（sessions/、cache/、state.db、.update_check、.hermes_history）瞬息万变且无恢复价值，会导致每次备份上千个文件。明确指定要备份的目录和文件。

### 首次全量备份是正常的
首次运行会备份所有 skills 文件（~80 个）和全部中转站代码。后续每天 Git 层自动去重（相同内容不存储新 blob），但目录结构保持完整——每天的快照都可独立恢复，无需拼接历史增量。

### 文件名含空格
`hermes agent` 文件夹名含空格，bash 中需引号包裹。JSON 中路径正常。
