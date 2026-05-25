# 不随 hermes backup 迁移的工具清单

以下工具安装在 `~/.hermes/` 之外，服务器重置/迁移后需要**手动重建**。

## 终端编程助手

| 工具 | 仓库 | 安装方式 |
|------|------|----------|
| CodeWhale (deepseek-tui) | `Hmbown/CodeWhale` | ① GitHub Release binary → `/usr/local/bin/codewhale` ② 源码 git clone + `cargo build --release` |
| DeepSeekCode | `willamhou/DeepSeekCode` | Release tar.gz → `/usr/local/bin/dscode` |
| Aider | `aider-chat` (pip) | `pip3 install aider-chat --break-system-packages` |

注意：Hmbown/CodeWhale 的 `deepseek-tui` 二进制只是别名，实际调用 `codewhale-tui`。需安装完整 `codewhale-tui` 或 `codewhale`。

## 凭证文件（需手动备份）

| 文件 | 内容 |
|------|------|
| `~/.github_token` | `export GITHUB_TOKEN=github_pat_xxx` |
| `~/.5sim_token` | `export FIVESIM_TOKEN=eyJ...` |

## API Relay 中转站

路径：`~/api-relay/` — 需单独备份（tar czf），或从 `api-relay` 技能模板重建。

## 代理配置

`/etc/mihomo/config.yaml` — 如需迁移，`sudo cp` 到备份目录再 scp。

## 迁移后重建顺序

1. 代理 (mihomo) → 2. Hermes restore → 3. API Relay → 4. Token 文件 → 5. 终端工具 → 6. Cron jobs
