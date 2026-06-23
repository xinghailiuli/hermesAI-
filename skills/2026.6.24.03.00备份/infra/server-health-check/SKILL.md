---
name: server-health-check
description: Check server health metrics (disk, memory, CPU) and service status (hermes gateway, API relay, proxy) for Hermes Agent cloud servers.
category: infra
---

# Server Health Check

Check the health of a Hermes Agent cloud server with standard metrics and service status.

## Triggers

- Periodic cron health checks
- User asks "check server health" / "服务器状态" / "is the server okay?"
- Post-deployment or post-migration verification

## Checks and Thresholds

| Check | Command | Healthy | Warning |
|-------|---------|---------|---------|
| Disk | `df -h /` | Use% ≤ 85% | > 85% |
| Memory | `free -h` | Available ≥ 500MB | < 500MB |
| CPU | `uptime` | 1min load ≤ cores×2 | > cores×2 |
| API Relay | `curl -s -o /dev/null -w "%{http_code}" --max-time 5 127.0.0.1:8848/health` | 200 | Non-200 or timeout |
| Hermes Gateway | `hermes gateway status` | systemd active running | inactive or repeated API errors |

## Key Pitfalls

### Hermes Gateway health check

**Do NOT** try to hit an HTTP health endpoint (e.g., `curl http://127.0.0.1:18080/health`). The gateway does NOT expose a TCP health endpoint — it connects outbound to messaging platforms and LLM APIs. Use the CLI instead:

```
hermes gateway status
```

This returns the systemd user service status, including uptime, memory usage, and recent log warnings. The gateway is a user-level systemd service (`systemctl --user`), not a system-level one.

### API errors in gateway logs are not server failures

The gateway logs may show SSL errors (`WRONG_VERSION_NUMBER`), stream stalling, or `RemoteProtocolError` when communicating with upstream LLM APIs (especially through proxies). These are transient retry-handled issues, not server health problems. Only flag the gateway if:

- The systemd service is not `active (running)`
- It has been failing ALL retries for an extended period (check log timestamps)
- Memory usage has grown unreasonably (e.g., > 2GB sustained)

### Proxy health

Mihomo/Clash Meta proxy runs as a user systemd service:

```
systemctl --user status mihomo
```

Even if the service shows a startup `bind: address already in use` error, the port may still be listening — verify with `ss -tlnp | grep 7897`.

## Report Format

- All clear: `今日服务器播报：良好`
- Problems found: `今日服务器播报：[具体问题描述]`
- Nothing to report: `[SILENT]`
