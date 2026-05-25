# Clash Verge (mihomo) 代理端口为 0 的案例

## 场景

用户坚称代理端口是 7897，但 WSL 怎么都连不上。排查发现：

1. netstat 显示没有 7890-7899 区间的任何端口在监听
2. 发现 `verge-mihomo.exe` 在监听 `0.0.0.0:9097`
3. curl 连 9097 报 `405 Method Not Allowed` → 这是 API 端口，不是代理端口
4. 查询 Clash API `/configs` 返回：

```json
{
  "port": 0,
  "socks-port": 0,
  "redir-port": 0,
  "tproxy-port": 0,
  "mixed-port": 0,
  "mode": "global",
  "allow-lan": true,
  "bind-address": "*"
}
```

所有代理端口都是 0 — Clash 虽然跑着，但根本没开代理端口。

## 诊断命令

```bash
# 找 Clash 进程 PID
powershell.exe -Command "Get-Process -Name '*mihomo*','*clash*' | Select-Object Id, ProcessName, Path"

# 查监听端口
powershell.exe -Command "Get-NetTCPConnection -OwningProcess 37552 -State Listen"

# 读 Clash 运行时配置
curl -s http://172.28.176.1:9097/configs
```

## 根因

用户需要在 Clash Verge GUI 里设置代理端口（HTTP/Mixed），当前为空（0）。
