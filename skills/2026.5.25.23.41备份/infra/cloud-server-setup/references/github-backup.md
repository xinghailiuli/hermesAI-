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

# 3. 安装 rsync（增量备份依赖）
sudo apt install -y rsync
```

**⚠️ Token 权限要求**：至少需要 `repo` scope（读写仓库）。如需 Star 收藏仓库则额外需要 `public_repo` scope。

## 备份脚本

脚本路径：`/home/admin/scripts/daily-backup-github.sh`

核心设计：
- 增量备份：用 `rsync -a --ignore-existing` 只复制变动文件
- 四类独立目录：阿罗娜角色、Skills、Hermes Agent 核心配置、中转站
- 无变更自动跳过（不推空提交）
- 时间戳精确到分钟：`YYYY.M.D.HH.MM备份`

```bash
#!/bin/bash
# 每日增量备份到 GitHub — 只备份当天有变动的文件
set -e

REPO_DIR="/home/admin/hermesAI-backup"
TIMESTAMP=$(date +%Y.%-m.%-d.%-H.%-M)
GH_TOKEN=$(cat /home/admin/.hermes/gh_token)

cd "$REPO_DIR"
git pull origin main -q 2>/dev/null

changed=0

backup_dir() {
  local SRC="$1" DST="$2" LABEL="$3"
  if [ ! -d "$SRC" ] || [ -z "$(ls -A "$SRC" 2>/dev/null)" ]; then return; fi
  mkdir -p "$DST"
  rsync -a --ignore-existing "$SRC/" "$DST/" 2>/dev/null
  if [ -n "$(ls -A "$DST" 2>/dev/null)" ]; then
    echo "  ✅ ${LABEL}"; changed=1
  else
    rm -rf "$DST"
  fi
}

backup_file() {
  local SRC="$1" DST_DIR="$2"
  if [ -f "$SRC" ]; then
    mkdir -p "$DST_DIR"; cp "$SRC" "$DST_DIR/"; changed=1
  fi
}

# 1. 阿罗娜角色
ARONA_DIR="阿罗娜角色/${TIMESTAMP}备份"
backup_file "/home/admin/.hermes/SOUL.md"     "$ARONA_DIR"
backup_file "/home/admin/.hermes/auth.json"   "$ARONA_DIR"
backup_file "/home/admin/.hermes/config.yaml" "$ARONA_DIR"

# 2. Skills
backup_dir "/home/admin/.hermes/skills/" "skills/${TIMESTAMP}备份" "Skills"

# 3. Hermes Agent
HERMES_DIR="hermes agent/${TIMESTAMP}备份"
backup_file "/home/admin/.hermes/cron/jobs.json"    "$HERMES_DIR"
backup_file "/etc/systemd/system/api-relay.service" "$HERMES_DIR"
backup_file "/etc/systemd/system/mihomo.service"    "$HERMES_DIR"
mkdir -p "$HERMES_DIR"
echo "=== $(date) ===" > "$HERMES_DIR/已安装工具.txt"
ls -lh /usr/local/bin/{claude,deepseek,codewhale,codewhale-tui} 2>/dev/null >> "$HERMES_DIR/已安装工具.txt"

# 4. 中转站
backup_dir "/home/admin/api-relay/" "中转站/${TIMESTAMP}备份" "中转站"

[ "$changed" -eq 0 ] && { echo "⏭️ 无变更"; exit 0; }

git add -A
git commit -m "📦 ${TIMESTAMP}备份" || exit 0
git push "https://USERNAME:${GH_TOKEN}@github.com/USER/hermesAI-.git" main

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
- 如需 Star 功能需重新生成带 `public_repo` 的 token

### 防止备份垃圾文件（关键！）
**不要 `cp -r .hermes/*`** 全量复制！运行时数据（sessions/、cache/、state.db、.update_check、.hermes_history）瞬息万变且无恢复价值，会导致每次备份上千个文件。明确指定要备份的目录和文件。

### 首次全量备份是正常的
首次运行可能备份所有 skills 文件（~80 个），后续每天仅增量几个变更文件。不要因首次文件多就修改备份策略。

### 文件名含空格
`hermes agent` 文件夹名含空格，bash 中需引号包裹。JSON 中路径正常。
