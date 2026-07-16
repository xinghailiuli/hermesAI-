# pipx vs venv 安装方案对比

## 当 pipx 失败时的兜底方案

### 适用场景

- pipx install 在低配服务器（1核1G）上 OOM 被杀
- pipx install 在编译 C 扩展时卡死
- pipx 与系统 Python 版本不兼容
- 用户已手改环境，pipx 路径混乱

### 完整 venv 安装流程

```bash
# 1. 创建 venv
python3.12 -m venv ~/hermes_env

# 2. 配置国内 pip 镜像（必备）
~/hermes_env/bin/pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/

# 3. 安装
~/hermes_env/bin/pip install hermes-agent

# 4. 添加到 PATH
sudo ln -sf ~/hermes_env/bin/hermes /usr/local/bin/hermes
# 或 export PATH="$HOME/hermes_env/bin:$PATH" 写入 ~/.bashrc

# 5. 验证
hermes --version
```

### pipx vs venv 对比

| 特性 | pipx | venv |
|------|------|------|
| 隔离性 | 每个工具独立 venv | 共享 venv |
| 安装速度 | 慢（多个 venv 创建+编译） | 较快（单 venv） |
| 内存占用 | 更高（多 venv 进程） | 较低 |
| 自动 PATH | pipx ensurepath | 需手动 ln/source |
| 与 systemd 配合 | 路径固定（~/.local/bin） | 需指定 venv bin 路径 |
| 卸载 | pipx uninstall | 直接删目录 |
| 低配服务器 | 容易 OOM | 更稳定 |

### 关键 Pitfalls

1. **不要混用 pipx 和 venv**：已有 pipx 安装时，`pipx uninstall hermes-agent` 清理后再建 venv
2. **venv python 不包含 ~/.local site-packages**：`~/hermes_env/bin/python` 的 sys.path 不含 USER_SITE，用 `--break-system-packages` 安装的模块不可见
3. **systemd 需指定 venv python 路径**：`ExecStart=/home/admin/hermes_env/bin/hermes gateway run`
