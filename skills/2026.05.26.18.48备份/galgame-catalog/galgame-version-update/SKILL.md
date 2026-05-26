---
name: galgame-version-update
description: Galgame年鉴网站更新标准流程。每次修改网站功能后执行此流程。
category: galgame-catalog
---

# Galgame 年鉴更新流程

## 触发条件
任何对 `galgame_catalog.html` 的功能性修改（bug修复、新功能、样式改动等）。

## 标准步骤

### 1. 修改网站文件
- 主文件：`C:\Users\Administrator\Desktop\galgame_catalog.html`（WSL路径：`/mnt/c/Users/Administrator/Desktop/galgame_catalog.html`）
- 资源目录：`C:\Users\Administrator\Desktop\galgame_assets/`

### 2. 记录更新日志
在下一次请求到来时，将本次所有改动追加到更新日志：
- 文件：`Desktop/galgame_versions/2026.5.21.1.29_原点版本/更新日志.txt`
- 格式：`【YYYY.M.D 更新记录】` 标题 + 每条改动一行 emoji + 说明
- 必须记录：bug修复、新增功能、资源变动

### 3. 同步到版本文件夹
```bash
cp "Desktop/galgame_catalog.html" "Desktop/galgame_versions/2026.5.21.1.29_原点版本/galgame_catalog.html"
```

### 4. 新建资源联结（如有新资源目录）
```powershell
New-Item -ItemType Junction -Path "版本文件夹/galgame_assets" -Target "Desktop/galgame_assets"
```

### 5. 重大更新建新版本文件夹
格式：`年.月.日.时.分_描述`（如 `2026.5.21.1.29_原点版本`）

### 6. 更新每日进度日志
同步追加到 `Desktop/galgame_versions/每日进度日志.md`
- 格式见 `daily-progress-log` skill
- 每次工作会话结束时执行

## 注意事项
- 用户偏好中文交流，所有日志用中文
- 每次修改后必须更新日志，用户会检查
- 桌面文件和版本文件夹要保持同步
- Windows文件系统操作通过 WSL `/mnt/c/` 路径
- PowerShell Junction 命令：`/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -Command "New-Item -ItemType Junction ..."`
