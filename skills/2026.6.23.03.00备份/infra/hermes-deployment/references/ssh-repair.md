# Broken SSH Repair (Ubuntu)

## Symptoms
- `systemctl is-active ssh` → inactive
- `systemctl start ssh` → "Dependency failed" or silent failure
- `dpkg -l openssh-server` → `un` (unknown/not-installed)
- `journalctl -xe -u ssh` → "Missing privilege separation directory: /run/sshd"
- SSH port 22 open but connection reset

## Fix Priority

### 1. Quick fix (missing /run/sshd)
```bash
mkdir -p /run/sshd
systemctl start ssh
```

### 2. Direct sshd (bypass systemd) — ⚠️ WARNING
If systemd still refuses, start sshd directly:
```bash
mkdir -p /run/sshd
/usr/sbin/sshd -D &
```
**⚠️ CRITICAL**: After this manual fix works, `systemctl start ssh` will FAIL with "Address already in use" because the manual `sshd` process holds port 22. To switch back to systemd: `pkill sshd && sleep 1 && systemctl start ssh`. Do NOT just leave both running — it creates a silent port conflict.

### 3. Package repair
If dpkg shows `un` status:
```bash
apt purge openssh-server -y
apt install openssh-server -y
systemctl start ssh
```

## Fallback Access
When SSH is completely broken, use Alibaba Cloud VNC console:
1. ECS Console → Instance → Remote Connection → VNC
2. Reset VNC password from console (no old password needed)
3. Login as root with the instance password

## Prevention
- Always run `hermes backup --quick` before touching system packages
- Cloud instance data lives at `/home/admin/.hermes/`
