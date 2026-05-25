---
name: wsl-proxy-setup
description: WSL2 代理配置与网络排障 — Clash Verge / mihomo 代理让 WSL 访问 GitHub 等外网
category: troubleshooting
---

# WSL 代理配置

从 WSL 访问 Windows 主机上运行的代理（Clash Verge / V2Ray 等），用于翻墙访问 GitHub 等被墙网站。

## 触发条件
- 用户在 WSL 中需要访问 GitHub 等被墙站点
- `curl` 超时或返回 000
- 用户提到"梯子""代理""翻墙""proxy"

---

## 推荐方案：TUN 模式（一步到位）

**Clash Verge 开 TUN 模式**（服务模式运行），所有流量透明代理。WSL 无需任何环境变量。

验证 TUN 生效：
```bash
curl -sv https://github.com 2>&1 | grep "Trying"
# 看到 198.18.0.x 即 Clash fake-ip，说明 TUN 在工作
```

如果 DNS 偶尔解析超时，等一会或重启 Clash 内核即可。

---

## 备选方案：显式 HTTP 代理端口

### 1. 先搞清楚端口

不要只问用户端口号——用户可能记错。直接从 WSL 查 Windows 监听端口：

```bash
# 查看 Windows 上非 127.0.0.1 的监听端口
powershell.exe -Command "netstat -ano | findstr LISTENING | findstr /V '127.0.0.1'"
```

找到可疑端口后，确认进程身份：
```bash
powershell.exe -Command "Get-Process -Id (Get-NetTCPConnection -LocalPort <PORT> -State Listen).OwningProcess | Select-Object Id, ProcessName, Path"
```

**重要**：Clash Verge 内核是 `verge-mihomo.exe`，其 API 端口固定为 **9097**（不是代理端口！）。API 端口返回 405 或 404 是正常的，只接受 `/configs` 等 REST 路径。

### 2. 查 Clash 运行时配置

```bash
curl -s http://172.28.176.1:9097/configs 2>&1 | python3 -c "
import sys,json
c=json.load(sys.stdin)
print(f'port: {c[\"port\"]}')
print(f'mixed-port: {c[\"mixed-port\"]}')
print(f'socks-port: {c[\"socks-port\"]}')
print(f'tun: {c[\"tun\"][\"enable\"]}')
print(f'allow-lan: {c[\"allow-lan\"]}')
print(f'mode: {c[\"mode\"]}')
"
```

如果 `port` 和 `mixed-port` 都是 **0**，说明没配代理端口——要么开 TUN 模式，要么在 Clash Verge 界面手动填端口号并**重启 Clash 内核**（只填不重启不生效）。

### 3. 测试连接

```bash
# 先试 127.0.0.1
curl -x http://127.0.0.1:<PORT> -I --connect-timeout 10 https://github.com

# 不通则试 WSL 网关 IP
WINDOWS_IP=$(grep nameserver /etc/resolv.conf | awk '{print $2}')
curl -x http://${WINDOWS_IP}:<PORT> -I --connect-timeout 10 https://github.com

# 再不通试 WSL 的 default gateway
WSL_GW=$(ip route show default | awk '{print $3}')
curl -x http://${WSL_GW}:<PORT> -I --connect-timeout 10 https://github.com
```

### 4. Windows 防火墙放行

如果端口可达但被拒，加防火墙规则：
```bash
powershell.exe -Command "New-NetFirewallRule -DisplayName 'ClashProxy' -Direction Inbound -Protocol TCP -LocalPort <PORT1>,<PORT2> -Action Allow"
```

### 5. 持久化

通了写入 `~/.bashrc`：
```bash
echo 'export HTTP_PROXY=http://127.0.0.1:<PORT>' >> ~/.bashrc
echo 'export HTTPS_PROXY=http://127.0.0.1:<PORT>' >> ~/.bashrc
```

---

## Pitfalls（踩坑记录）

- **不要一根筋**：某 IP:端口不通，立刻换 IP、换端口、或直接切 TUN 模式。反复用同一参数 curl 是浪费时间
- **Clash API 返回 405 = 正常**：9097 是管理端口，不接受 CONNECT tunnel，不是代理挂了
- **端口全是 0 = TUN 在跑或没配**：先查 `/configs`，再看是否 TUN 模式已工作
- **用户说的端口不一定对**：用 `netstat` 从 Windows 侧验证实际监听端口，不要仅靠用户口述
- **WSL2 127.0.0.1 不一定转发到 Windows**：多备几个 IP（127.0.0.1、nameserver IP、WSL gateway IP、Windows LAN IP）
- **填了端口要点重启**：Clash Verge 界面修改端口后不点"重启 Clash 内核"不会生效
- **DNS 偶尔超时 = Clash fake-ip 缓存**：TUN 模式下偶发，等几秒或重启内核解决
