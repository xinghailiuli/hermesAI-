---
name: wsl-troubleshooting
description: WSL2 环境下与 Windows 主机交互的网络/代理/端口排查流程。不要一根筋重试——换IP、换端口、换方向。
triggers:
  - WSL 中无法连接 Windows 上的服务（代理、数据库等）
  - 代理/网络不通
  - 需要从 WSL 访问 Windows 主机端口
  - 用户说用了代理但连不上
---

# WSL 网络排查

WSL2 是独立虚拟机，与 Windows 不在同一网络栈。排查连接问题时有固定流程。

## 关键网络地址

```bash
# WSL 视角下的 Windows 主机 IP（resolv.conf）
grep nameserver /etc/resolv.conf | awk '{print $2}'

# WSL 网关 IP（通常也是 Windows）
ip route show default | awk '{print $3}'

# Windows 自身局域网 IP（也可能可达）
```

- `127.0.0.1` 在 WSL2 中指向 WSL 自身，不是 Windows
- WSL2 新版有 localhost 转发但不总是可靠

## 代理排查流程

### 第 1 步：验证端口（不要信记忆）

用户可能记错端口号。**不要反复重试同一个错误端口**。先用 netstat 确认：

```bash
# 列出 Windows 上所有非 localhost 的监听端口
powershell.exe -Command "netstat -ano | findstr LISTENING | findstr /V '127.0.0.1'"
```

### 第 2 步：找到代理进程

```bash
# 按进程名找 PID
powershell.exe -Command "Get-Process -Name '*mihomo*','*clash*' | Select-Object Id, ProcessName, Path"

# 查该 PID 的监听端口
powershell.exe -Command "Get-NetTCPConnection -OwningProcess <PID> -State Listen | Select-Object LocalAddress, LocalPort"
```

### 第 3 步：区分 API 端口 vs 代理端口

Clash/mihomo 有两个端口：
- **API 管理端口**（通常 9090/9097）：curl 代理 HTTPS 时报 `405 Method Not Allowed`
- **代理端口**（HTTP/SOCKS/Mixed）：真正转发流量的端口

如果连上了但报 405，说明连到了 API 端口。查 Clash 实际代理配置：

```bash
curl -s http://<IP>:<API_PORT>/configs | python3 -c "import sys,json; c=json.load(sys.stdin); print(f'http={c[\"port\"]}, socks={c[\"socks-port\"]}, mixed={c[\"mixed-port\"]}')"
```

如果所有代理端口都是 0 → Clash 没配置代理端口（可能在用 TUN 模式，或 GUI 没设端口）。

### 第 4 步：按优先级测试连通

```bash
# 1. WSL 网关 IP
GW=$(ip route show default | awk '{print $3}')
curl -x http://$GW:<PORT> -I https://github.com

# 2. resolv.conf 中的 Windows IP
WIP=$(grep nameserver /etc/resolv.conf | awk '{print $2}')
curl -x http://$WIP:<PORT> -I https://github.com

# 3. 127.0.0.1（localhost 转发）
curl -x http://127.0.0.1:<PORT> -I https://github.com
```

### 第 5 步：防火墙放行

端口存在但连不上 → Windows 防火墙拦了：

```bash
powershell.exe -Command "New-NetFirewallRule -DisplayName 'ProxyRule' -Direction Inbound -Protocol TCP -LocalPort <PORT> -Action Allow"
```

## 常见软件端口

| 软件 | 默认代理端口 | 默认 API 端口 |
|------|-------------|-------------|
| Clash Verge (mihomo) | 7890 | 9097 |
| V2RayN | 10809 | 10808 |

## Pitfalls

- **用户记错端口号**极其常见——永远先用 netstat 验证，别盲试
- **API 端口 ≠ 代理端口**——405 = 连到管理端口了
- **"允许局域网"必须开**——梯子默认只绑 127.0.0.1
- **Windows 防火墙默认拦入站**——即使梯子开了 LAN
- **不要一根筋**——同一方法连试 2 次不通就换 IP/换端口/换方向
