# Zombie Process Recovery — Dependencies Lost

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

## Prevention

- **Prefer project-level venv** (`~/api-relay/venv/`) over `pip3 install --break-system-packages`
- If using systemd, set `ExecStart=%h/api-relay/venv/bin/python %h/api-relay/server.py`
- Add a cron health check that tests the actual port (from config.json), not the default 8848
