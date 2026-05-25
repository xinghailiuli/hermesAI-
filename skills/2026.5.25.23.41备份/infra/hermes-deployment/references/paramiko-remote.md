# 使用 Paramiko 自动化远程部署

当 `sshpass` 不可用（未安装或无 sudo 权限）时，用 Python paramiko 替代。

> ⚠️ **SSH 彻底不通时**：如果 `Connection reset by peer` / `Error reading SSH protocol banner`，说明目标服务器的 sshd 本身已损坏（非密码问题）。此时 paramiko 也无能为力。唯一入口是 **云厂商 VNC 控制台**（阿里云：ECS 控制台 → 远程连接 → VNC → 救援模式）。

## 安装

```bash
python3 -m pip install paramiko scp
```

## 连接模板

```python
import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('host', username='root', password='xxx', timeout=15)
```

## 执行命令

```python
# 简单命令
stdin, stdout, stderr = ssh.exec_command('hermes --version')
print(stdout.read().decode())

# 需要 PATH 的命令（pipx 安装的 hermes 不在 root 默认 PATH）
stdin, stdout, stderr = ssh.exec_command('export PATH=$PATH:/root/.local/bin && hermes --version')
print(stdout.read().decode())
```

## 实时读取输出的命令

```python
import time

channel = ssh.get_transport().open_session()
channel.get_pty()  # 获取 PTY 以支持伪终端输出
channel.exec_command('command here')

chunks = []
start = time.time()
while time.time() - start < 120:
    if channel.recv_ready():
        data = channel.recv(8192).decode()
        print(data, end='', flush=True)
    if channel.exit_status_ready():
        break
    time.sleep(0.5)

print(f"RC: {channel.recv_exit_status()}")
```

## SCP 上传文件

```python
from scp import SCPClient

with SCPClient(ssh.get_transport()) as scp:
    scp.put('/local/path/file.zip', '/remote/path/file.zip')
```

## 完整数据同步流程（云端 → 本地）

当无法用 `hermes backup` + `scp` 时（如 SSH 部分损坏），直接用 paramiko SFTP 搬运核心文件：

```python
import paramiko, os, subprocess

host, password = "X.X.X.X", "your_password"

s = paramiko.SSHClient()
s.set_missing_host_key_policy(paramiko.AutoAddPolicy())
s.connect(host, username="root", password=password, timeout=10)

# 1. 远端打包核心数据
s.exec_command(
    "cd ~ && tar czf /tmp/hermes-data.tar.gz "
    ".hermes/config.yaml .hermes/.env .hermes/memories/ "
    ".hermes/skills/ .hermes/sessions/ .hermes/cron/ "
    ".hermes/auth.json .hermes/channel_directory.json"
)

# 2. SFTP 下载到本地
sftp = s.open_sftp()
sftp.get("/tmp/hermes-data.tar.gz", "/tmp/hermes-data.tar.gz")
sftp.close()

# 3. 本地解压
subprocess.run(["tar", "xzf", "/tmp/hermes-data.tar.gz",
                "-C", os.path.expanduser("~")], check=True)

# 4. 重启本地网关生效
s.close()
```

> 🔑 **关键检查项**：同步后务必验证 `~/.hermes/memories/MEMORY.md`、`USER.md` 已落地。重启网关后新记忆才会加载。

## SFTP 下载文件（无需 scp 包）

```python
sftp = ssh.open_sftp()
sftp.get("/remote/path/file.tar.gz", "/local/path/file.tar.gz")
sftp.close()
```

## tar 解压（数据同步后还原）

```python
import subprocess
local_hermes = os.path.expanduser("~/.hermes")
subprocess.run(["tar", "xzf", "/tmp/hermes-data.tar.gz", "-C", local_hermes])
```

## 后台进程（nohup）

```python
channel = ssh.get_transport().open_session()
channel.exec_command('export PATH=$PATH:/root/.local/bin && nohup hermes gateway run > /root/hermes-gateway.log 2>&1 &')
```

> 生产环境推荐用 systemd 而非 nohup，见 SKILL.md 步骤 5。
