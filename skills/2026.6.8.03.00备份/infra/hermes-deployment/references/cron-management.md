# Hermes Cron 任务管理

## deliver 参数陷阱

### `deliver: "origin"` 的坑

`origin` 会解析为 **cron 任务创建时所在的平台**，而非用户当前活跃平台。

**典型场景**：
- 用户在微信上创建了「服务器每日播报」等 cron 任务
- 后来主要使用 QQ
- 任务继续发往微信，QQ 侧悄无声息

**修复**：显式指定平台名

```bash
# 查看当前 deliver 设置
hermes cron list

# 改为 QQ
hermes cron update <job_id> --deliver qqbot

# 改为微信
hermes cron update <job_id> --deliver weixin
```

### 常用 deliver 值

| 值 | 含义 |
|----|------|
| `origin` | 自动检测创建平台（**慎用**，切换平台后不会跟随） |
| `qqbot` | QQ Bot |
| `weixin` | 微信 |
| `telegram` | Telegram |
| `discord` | Discord |
| `local` | 仅本地保存，不投递到任何平台 |

### 批量修改

如果多个任务都需要改平台：

```bash
# 列出所有任务及其 deliver
hermes cron list

# 逐个更新（cron update 接受 --deliver）
for id in <id1> <id2> <id3>; do
  hermes cron update "$id" --deliver qqbot
done
```

### 预防措施

创建 cron 任务时直接指定 `--deliver`，不要依赖 `origin` 的自动解析：

```bash
hermes cron create "..." --deliver qqbot
```

## 标准 Cron 任务清单

部署/恢复时应重建以下 7 个任务（全部来自 `xinghailiuli/hermesAI-` 仓库备份）：

| 名称 | 调度 | deliver | 用途 |
|------|------|---------|------|
| GitHub每日备份 | `0 3 * * *` | origin | no_agent，脚本 `github-daily-backup.py` |
| 中转站每日备份 | `0 3 * * *` | local | cp -r ~/api-relay/ → ~/api-relay-backups/ |
| Hermes每日备份 | `0 4 * * *` | local | hermes backup -o ... |
| 服务器每日播报 | `0 9 * * *` | origin | 系统状态日报 |
| Galgame新作速报 | `0 10 * * *` | origin | VNDB API 新游戏 |
| 轻小说更新速报 | `0 11 * * *` | origin | lightnovel.cn 监测 |
| 服务器晚间播报 | `0 20 * * *` | origin | API 统计夜报 |
| 中转站健康监控 | `*/30 * * * *` | origin | curl 127.0.0.1:8848/health |

使用 `cronjob(action="create", ...)` 工具逐个恢复，不要用 `hermes cron create` CLI（它不支持 no_agent/script 等高级参数）。
