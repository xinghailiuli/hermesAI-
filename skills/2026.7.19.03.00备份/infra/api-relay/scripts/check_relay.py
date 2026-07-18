#!/usr/bin/env python3
"""Quick health check for API relay.

Auto-detects Flask relay port and reports status.
Exit code: 0 = healthy, 1 = unhealthy.
Useful for cron monitoring scripts.

Usage:
    python3 check_relay.py
    python3 check_relay.py --port 8847   # force specific port

Cron job usage (silent-on-healthy pattern):
    python3 ~/.hermes/skills/infra/api-relay/scripts/check_relay.py \
        && exit 0 \
        || echo "API Relay 异常，请检查"

    # Or use cron job's [SILENT] convention:
    # health check script; if unhealthy, cron agent reports;
    # if healthy, cron agent responds [SILENT] to suppress delivery.
"""
import argparse
import json
import urllib.request
import urllib.error
import subprocess
import sys
import re

# Known relay ports in priority order
KNOWN_PORTS = [8847, 8848]


def detect_port():
    """Find Flask relay port by inspecting listening sockets.

    The relay process may show as 'python3' in ss output (not necessarily
    'server.py' in the cmdline), so we match any python process listening
    on our known relay ports.
    """
    try:
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True, text=True, timeout=5
        )
        # Look for python processes on known relay ports
        for line in result.stdout.splitlines():
            if "python" in line:
                m = re.search(r'127\.0\.0\.1:(88[14][78])', line)
                if m:
                    return int(m.group(1))
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def check_health(port):
    url = f"http://127.0.0.1:{port}/health"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode()
            data = json.loads(body)
            if data.get("status") == "ok":
                print(f"HEALTHY | port={port} | models={data.get('models', '?')}")
                return True
            else:
                print(f"UNHEALTHY | port={port} | unexpected response: {body[:200]}")
                return False
    except urllib.error.URLError as e:
        print(f"FAILED | port={port} | {e.reason}")
        return False
    except (json.JSONDecodeError, TimeoutError) as e:
        print(f"FAILED | port={port} | {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Check API relay health")
    parser.add_argument("--port", type=int, help="Flask port (auto-detect if omitted)")
    args = parser.parse_args()

    # User-specified port takes priority
    if args.port:
        if check_health(args.port):
            return 0
        print(f"NO_RELAY_FOUND | specified port {args.port} failed")
        sys.exit(1)

    # Auto-detect from listening sockets
    port = detect_port()
    if port and check_health(port):
        return 0

    # Fallback: try all known ports
    for p in KNOWN_PORTS:
        if check_health(p):
            return 0

    print("NO_RELAY_FOUND | no python server.py process listening on common ports")
    sys.exit(1)


if __name__ == "__main__":
    main()
