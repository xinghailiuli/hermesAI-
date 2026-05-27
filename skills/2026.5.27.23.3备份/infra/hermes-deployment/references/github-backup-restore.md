# GitHub 备份恢复

从 GitHub 备份仓库 `xinghailiuli/hermesAI-` 恢复 Hermes 数据到本地。

## 前置条件

- GitHub PAT Token 已配置（见 `github-backup-sync.md` 的 Token 管理）
- 本地 Git credential 已设置：
  ```bash
  git config --global credential.helper 'store --file ~/.git-credentials'
  echo "https://xinghailiuli:<TOKEN>@github.com" > ~/.git-credentials
  chmod 600 ~/.git-credentials
  ```

## 恢复流程

### 步骤 1：克隆备份仓库

```bash
cd /tmp
git clone https://github.com/xinghailiuli/hermesAI-.git
# 如果此仓库为空（仅占位），则 clone hermesAI-：
git clone https://github.com/xinghailiuli/hermesAI-.git
```

### 步骤 2：识别最新备份

备份按时间戳目录组织，格式为 `YYYY.M.D.HH.MM备份`。选择各分类的最新备份：

```bash
cd /tmp/hermesAI-

# 查看各分类的最新备份
ls -d hermes\ agent/*备份/ | sort | tail -3
ls -d skills/*备份/ | sort | tail -3
ls -d 阿罗娜角色/*备份/ | sort | tail -3
ls -d 中转站/*备份/ | sort | tail -3
```

### 步骤 3：恢复技能（Skills）

```bash
# 将最新版本复制到 ~/.hermes/skills/
LATEST_SKILLS=$(ls -d skills/*备份/ | sort | tail -1)
mkdir -p ~/.hermes/skills/infra
cp -r "$LATEST_SKILLS"infra/* ~/.hermes/skills/infra/
```

### 步骤 4：恢复角色配置（SOUL.md + config.yaml）

```bash
mkdir -p ~/.hermes/characters

# 普拉娜（Plana）角色
LATEST_HERMES=$(ls -d "hermes agent/"*备份/ | sort | tail -1)
cp "$LATEST_HERMES/SOUL.md" ~/.hermes/characters/plana-soul.md 2>/dev/null
cp "$LATEST_HERMES/config.yaml" ~/.hermes/characters/plana-config.yaml 2>/dev/null

# 阿罗娜（Arona）角色
LATEST_ARONA=$(ls -d 阿罗娜角色/*备份/ | sort | tail -1)
cp "$LATEST_ARONA/SOUL.md" ~/.hermes/characters/arona-soul.md 2>/dev/null
cp "$LATEST_ARONA/config.yaml" ~/.hermes/characters/arona-config.yaml 2>/dev/null
```

### 步骤 5：恢复 Cron 定时任务

从备份的 `jobs.json` 读取任务定义，用 `cronjob(action="create")` 逐个重建：

```bash
# 查看备份中的 cron 任务
cat "hermes agent/"*备份/jobs.json 2>/dev/null | python3 -m json.tool | grep -E '"name"|"expr"'
```

常见任务：
| 名称 | 调度 | 用途 |
|------|------|------|
| 中转站每日备份 | `0 3 * * *` | 备份 ~/api-relay/ → ~/api-relay-backups/ |
| 服务器每日播报 | `0 9 * * *` | 系统状态日报 |
| 中转站健康监控 | `*/30 * * * *` | curl health check |
| Hermes 每日备份 | `0 4 * * *` | hermes backup |
| Galgame 新作速报 | `0 10 * * *` | VNDB 新游戏 |
| 轻小说更新速报 | `0 11 * * *` | lightnovel.cn 更新 |
| 服务器晚间播报 | `0 20 * * *` | API 统计夜报 |

### 步骤 6：恢复持久记忆

从备份配置中提取关键信息写入 memory：

- 用户偏好（语言、角色、称呼）
- 环境配置（providers、API 密钥位置、插件）
- GitHub 用户信息

### 步骤 7：清理

```bash
rm -rf /tmp/hermesAI-
# 或保留 credential 供后续 git 操作
```

## 注意事项

- **auth.json 不在 GitHub 备份中**（安全策略），需要从 live 系统或 .env 恢复 API 密钥
- **hermes-2026XXXX.zip** 是 hermes backup 的完整包，可直接 `hermes import` 恢复，比逐文件恢复更快
- **两个备份仓库**：`hermes-`（可能为空占位）和 `hermesAI-`（完整备份），先查 hermesAI-
