# WSL2 Proxy Setup: Clash Verge

## Problem

WSL2 is a virtual machine — it cannot reach `127.0.0.1` on the Windows host directly in some configurations. Proxy software (Clash, V2Ray) running on Windows may not be accessible from WSL.

## Diagnosis Steps

### 1. Check if proxy port is actually listening on Windows

```bash
powershell.exe -Command "netstat -ano | findstr LISTENING"
```

Look for the proxy process ports. For Clash Verge, the process is `verge-mihomo.exe`.

### 2. Find what ports the proxy process owns

```bash
powershell.exe -Command "Get-NetTCPConnection -OwningProcess <PID> -State Listen | Select LocalAddress,LocalPort"
```

### 3. Check if the API/config port differs from the proxy port

Clash Verge exposes an API port (commonly 9097) for its REST API. This is NOT the proxy port. Query the config:

```bash
curl http://172.28.176.1:9097/configs
```

Field `"port":0, "socks-port":0, "mixed-port":0` means NO proxy ports configured — TUN mode is active instead.

### 4. The WSL gateway IP

```bash
ip route show default | awk '{print $3}'
# Usually 172.28.176.1
```

Try both `127.0.0.1` and the gateway IP when testing proxy connectivity.

### 5. Windows IPs reachable from WSL

```
127.0.0.1          — localhost forwarding (works if WSL localhostForward=true)
172.28.176.1       — WSL gateway (virtual switch)
10.255.255.254     — nameserver from /etc/resolv.conf
192.168.x.x        — Windows LAN IP (from netstat output)
```

## Solutions (in order of effectiveness)

### A. TUN Mode (recommended)

Enable TUN mode in Clash Verge. This creates a virtual network interface that transparently proxies ALL traffic — no explicit HTTP_PROXY needed. WSL traffic will route through TUN automatically.

- Pro: No proxy env vars needed
- Pro: All tools (curl, git, pip, npm) work without config
- Con: May conflict with some VPNs

Verify TUN is working: check if `github.com` resolves to `198.18.0.x` (Clash fake-ip range).

### B. System Proxy

Enable Windows system proxy. WSL can piggyback on it if:
- Proxy software is set to listen on `0.0.0.0` (not just `127.0.0.1`)
- Windows Firewall allows inbound on the proxy port
- `Allow LAN` is enabled in the proxy software

### C. Explicit HTTP_PROXY

```bash
export HTTP_PROXY=http://WINDOWS_IP:PROXY_PORT
export HTTPS_PROXY=http://WINDOWS_IP:PROXY_PORT
```

Requires knowing the correct Windows IP (from step 4) and proxy port.

## Common Gotchas

- **Port confusion**: Clash API port ≠ Clash proxy port. The API responds with HTTP 405 to CONNECT requests.
- **Firewall**: Even with `Allow LAN` on, Windows Firewall may block inbound. Use:
  ```powershell
  New-NetFirewallRule -DisplayName "Clash" -Direction Inbound -Protocol TCP -LocalPort 7890,7897 -Action Allow
  ```
- **Bind address**: Proxy must bind to `0.0.0.0` or `*`, not just `127.0.0.1`. Check `bind-address` in Clash config.
- **Clash Verge config**: Port settings may read `0` in the API config but be set by the GUI at runtime. If API shows all ports as 0, the GUI settings haven't applied — restart the Clash kernel.
- **Fake-IP DNS**: When TUN is active, DNS resolves to fake IPs like `198.18.0.15`. This is normal — Clash intercepts and routes them. If DNS times out for some domains but works for others, the DNS is leaking — check TUN DNS settings.
