# 非交互式 SSH 密码输入：Python PTY 技巧

当 `sshpass` 和 `expect` 都不可用时（如 Hermes sandbox 执行环境），用 Python `pty.openpty()` 创建伪终端来自动输入 SSH 密码。

## 适用场景

- 需要 SSH 到服务器但只有密码（无密钥）
- 环境没有 `sshpass`、`expect`、`pexpect`
- 在 `execute_code` 沙箱或受限终端中运行

## 代码模板

```python
import subprocess
import os
import pty
import time
import select

password = "YOUR_PASSWORD"
host = "YOUR_SERVER_IP"
user = "root"

master_fd, slave_fd = pty.openpty()

proc = subprocess.Popen(
    ["ssh", "-o", "StrictHostKeyChecking=accept-new",
     "-o", "ConnectTimeout=10", f"{user}@{host}"],
    stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
    close_fds=True
)
os.close(slave_fd)

output = b""
password_sent = False
start_time = time.time()

while time.time() - start_time < 20:
    r, _, _ = select.select([master_fd], [], [], 1.0)
    if r:
        data = os.read(master_fd, 4096)
        if not data:
            break
        output += data
        decoded = output.decode('utf-8', errors='replace')

        if not password_sent and "password:" in decoded.lower():
            os.write(master_fd, (password + "\n").encode())
            password_sent = True

        # 检查是否拿到 shell prompt
        if password_sent:
            last_line = decoded.strip().split("\n")[-1] if decoded.strip() else ""
            if last_line.endswith("$ ") or last_line.endswith("# "):
                # 已登录，发命令
                os.write(master_fd, b"hostname && whoami && uptime && ip a | grep 'inet '; exit\n")
                time.sleep(2)
                while True:
                    r2, _, _ = select.select([master_fd], [], [], 2.0)
                    if r2:
                        d = os.read(master_fd, 4096)
                        if d:
                            output += d
                        else:
                            break
                    else:
                        break
                break

os.close(master_fd)
proc.wait()
print(output.decode('utf-8', errors='replace'))
```

## 要点

- `pty.openpty()` 是关键 — 模拟真实终端，SSH 才会走 password 认证而非 `ssh-askpass`
- `select.select()` 做非阻塞读取，避免死等
- 检测到 `password:` 提示后立即发送密码
- 登录成功后检测 `$ ` 或 `# ` 提示符确认已进入 shell
- 20 秒超时兜底，避免永久卡住

## 局限性

- 只能处理 "password:" 纯文本提示，不支持键盘交互（keyboard-interactive）的复杂场景
- 密码中的特殊字符（`$`、`!` 等）在某些 shell 下可能被解释，但通过 `pty` 发送通常安全
- 如果服务器配置了 `PasswordAuthentication no`，此方法无效
