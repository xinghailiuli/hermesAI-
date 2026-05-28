# jobs.json 字段说明

从备份中恢复的定时任务 JSON 格式。以下是关键字段：

```json
{
  "jobs": [
    {
      "id": "b0bd319e58d3",          // 旧 job ID（恢复后会有新 ID）
      "name": "中转站每日备份",       // → cronjob name
      "prompt": "备份API中转站...",   // → cronjob prompt
      "schedule": {
        "kind": "cron",
        "expr": "0 3 * * *",         // → cronjob schedule
        "display": "0 3 * * *"
      },
      "deliver": "local",            // → cronjob deliver
      "enabled": true,
      "enabled_toolsets": null,      // → cronjob enabled_toolsets (if set)
      "workdir": null,               // → cronjob workdir (if set)
      "skills": []                   // → cronjob skills (if set)
    }
  ]
}
```

## deliver 值含义

| 值 | 含义 |
|----|------|
| `"origin"` | 推送到当前对话（默认） |
| `"local"` | 仅保存，不推送 |
| `"all"` | 推送到所有已连接平台 |

## 恢复注意事项

- 旧 `id` 不可复用，每次 `cronjob create` 会生成新 ID
- `context_from` 字段引用旧 job ID，恢复后需要手动更新
- `deliver: "local"` 的任务（如备份任务）不需推送到对话
- `deliver: "origin"` 的任务（如每日播报）应推送到当前对话
