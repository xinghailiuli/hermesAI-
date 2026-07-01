# Zombie Process Recovery

Two distinct zombie scenarios can affect the API relay:

## Scenario A: Dependencies Lost (Port Not Bound)

## Symptoms

```
$ curl -s --max-time 10 127.0.0.1:8847/health
# → Connection refused (exit code 7)

$ ps aux | grep server.py
# → Process exists, running for days

$ ss -tlnp | grep python
# → No listening socket for server.py

$ ls /proc/<PID>/fd/
# → Only 0 1 2 3 — no socket file descriptors

$ cat /proc/<PID>/status | grep State
# → State: S (sleeping)
```

Process is alive (sleeping) but has no bound socket — Flask failed to start. The old process image persists because nothing killed it after the error.

## Root Cause

`pip3 install flask requests --break-system-packages` installed into system site-packages. After a system Python update, venv activation, or other environment change, those modules disappeared from `sys.path`. The system `python3` can no longer `import flask`, so `app.run()` fails silently (or prints to stderr that's not captured).

## Recovery Steps

```bash
# 1. Kill all stale processes
pkill -f "python.*server.py"
sleep 1

# 2. Create or repair the project venv
cd ~/api-relay
python3 -m venv venv
./venv/bin/pip install flask requests

# 3. Test with foreground (not background) to capture startup errors
./venv/bin/python server.py
# → * Serving Flask app 'server'
# → * Debug mode: off
# → * Running on http://127.0.0.1:8847

# 4. Kill the test, then background-launch properly
# (use terminal background=true)
```

## Verification

```bash
sleep 2
curl -s --max-time 5 127.0.0.1:8847/health
# → {"status":"ok","models":6}
```

## Prevention (Both Scenarios)

- **Prefer project-level venv** (`~/api-relay/venv/`) over `pip3 install --break-system-packages`
- If using systemd, set `ExecStart=%h/api-relay/venv/bin/python %h/api-relay/server.py`
- Add a cron health check that tests the actual port (from config.json), not the default 8848
- **Add port cleanup to systemd service** to auto-kill stale socket holders before starting

## Scenario B: Port Occupied by Zombie Process

## Symptoms

```
$ curl -s --max-time 10 127.0.0.1:8847/health
# → Connection refused (exit code 7)

$ ps aux | grep server.py
# → Process exists (the zombie, holding the port)

$ ss -tlnp | grep 8847
# → NO OUTPUT — ss doesn't see a listen socket

$ lsof -i :8847
# → Shows a python process (PID X) in LISTEN state
#   This is the zombie: it has the socket but isn't actually serving

$ systemctl --user status api-relay
# → * api-relay.service - API Relay Server
#      Active: activating (auto-restart) (Result: exit-code)
#      Main process exited, code=exited, status=1/FAILURE
#      NRestarts: 8444  ← keeps increasing rapidly
#
#   journalctl shows:
#   "Address already in use"
#   "Port 8847 is in use by another program"
```

**Root Cause**: An old process (leftover from a bare `python3 server.py` launch, a crashed instance, or system reboot with lingering socket) still holds the port. systemd tries to start → gets EADDRINUSE → exits with code 1 → systemd restarts → infinite loop.

**Key Diagnostic Difference From Scenario A**:
- Scenario A: `ss -tlnp | grep python` shows **nothing** (correct — no socket on any port)
- Scenario A: `lsof -i :PORT` shows **nothing** (correct — no process owns the port)
- Scenario B: `ss -tlnp | grep python` may show **nothing** (zombie is dead, just socket lingers)
- Scenario B: `lsof -i :PORT` shows the **zombie PID** still holding the port
- **Difference**: Scenario A has no active socket holder; Scenario B has one on the port. Always check `lsof -i :PORT` in addition to `ss -tlnp`.

## Recovery (Scenario B)

```bash
# 1. Kill the zombie holding the port
PID=$(lsof -ti :8847)   # -ti = numeric PID only
kill -9 $PID

# 2. Restart the service
systemctl --user restart api-relay

# 3. Verify
sleep 2
curl -s --max-time 5 http://127.0.0.1:8847/health
# → {"status":"ok","models":6}
```

**Note**: `pkill -f "python.*server.py"` may NOT kill the zombie if its command line doesn't match typical patterns. Use `lsof -ti :PORT` for guaranteed targeting.

## Prevention (Scenario B)

In systemd service unit, add an `ExecStartPre` to clear the port before starting:

```ini
[Service]
ExecStartPre=/bin/bash -c 'fuser -k 8847/tcp 2>/dev/null || true'
```

This automatically kills any zombie holding the port before systemd starts the new instance.
