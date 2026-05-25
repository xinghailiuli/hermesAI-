---
name: wsl-proxy
description: Configure WSL2 to use a Windows-hosted proxy (Clash/V2Ray/etc.) for internet access from behind the GFW.
triggers:
  - "WSL can't reach the internet"
  - "proxy on Windows not accessible from WSL"
  - "curl from WSL times out to external sites"
  - "need to route WSL traffic through Windows proxy"
---

# WSL2 → Windows Proxy Setup

When the user runs a proxy (Clash, V2Ray, SSR) on Windows and needs WSL2 to use it for internet access.

## Diagnostic Flow

Run these in order, stop at first success:

### 1. Verify internet access
```bash
curl -s --connect-timeout 5 -o /dev/null -w "%{http_code}" https://www.baidu.com
```
If this returns 200, WSL has direct internet — proxy not needed. If 000/timeout, continue.

### 2. Find Windows host IP from WSL
```bash
# Method A: WSL gateway (most reliable for WSL2)
ip route show default | awk '{print $3}'

# Method B: nameserver (fallback)
grep nameserver /etc/resolv.conf | awk '{print $2}'
```
Use the gateway IP (typically `172.x.x.1`) first, then try `127.0.0.1`.

### 3. Test proxy connectivity
```bash
curl -x http://<WINDOWS_IP>:<PORT> -I --connect-timeout 10 https://github.com
```

**Try these in order** (only 2-3 attempts total, don't loop):
| IP | When it works |
|----|---------------|
| `127.0.0.1` | WSL2 localhost forwarding (default in recent WSL2) |
| Gateway IP (`172.x.x.1`) | WSL2 bridged/NAT mode |
| Nameserver IP | WSL2 resolv.conf forwarding |

## Common Failure Modes

### Firewall Blocking (most common)
Windows Firewall blocks inbound connections from WSL to the proxy port.

**Fix** — PowerShell as Administrator on Windows:
```powershell
New-NetFirewallRule -DisplayName "Clash Proxy" -Direction Inbound -Protocol TCP -LocalPort <PORT> -Action Allow
```

### Proxy Bind Address
Proxy only listens on `127.0.0.1`, not `0.0.0.0`. WSL2 is a VM — `127.0.0.1` from WSL is NOT Windows' `127.0.0.1`.

**Fix** — Enable "Allow LAN" in proxy software:
- **Clash Verge**: Settings → Allow LAN
- **V2RayN**: Settings → Allow LAN connections
- **Clash for Windows**: Home → Allow LAN toggle

This makes the proxy listen on `0.0.0.0` (all interfaces), not just localhost.

### Port Mismatch
User may misremember the port. Common defaults:
- Clash: 7890 (HTTP), 7893 (SOCKS5), 7897 (mixed in some configs)
- V2Ray: 10809 (HTTP), 10808 (SOCKS5)

If 7897 fails, suggest trying 7890. Ask user to verify in proxy dashboard.

## Persisting the Config

Once proxy works, persist in `~/.bashrc`:
```bash
echo 'export HTTP_PROXY=http://127.0.0.1:<PORT>' >> ~/.bashrc
echo 'export HTTPS_PROXY=http://127.0.0.1:<PORT>' >> ~/.bashrc
```

## Quick Diagnostic Script

Run `scripts/diagnose.sh [PORT]` to automatically test connectivity. Defaults to port 7897.

```bash
bash ~/.hermes/skills/troubleshooting/wsl-proxy/scripts/diagnose.sh 7897
```

## Pitfalls

- **Don't spam retries.** If 127.0.0.1:PORT fails twice, the port is not reachable from WSL. Move to firewall/bind-address fixes — retrying the same curl won't help.
- **WSL2 vs WSL1.** In WSL1, `127.0.0.1` works because WSL1 shares the Windows network stack. In WSL2, it's a VM — use the gateway IP or ensure localhost forwarding is working.
- **Windows build matters.** WSL2 localhost forwarding requires Windows 10 build 18945+ or Windows 11. Older builds need the gateway IP approach exclusively.
- **Don't assume port.** Users often misremember proxy ports (9897 → 7897 → 7890). If a port fails, ask once to verify in the proxy dashboard, then move on.
