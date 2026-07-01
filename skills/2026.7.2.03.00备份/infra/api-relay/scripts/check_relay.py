#!/usr/bin/env python3
"""Quick health check for API relay.

Auto-detects Flask relay port and reports status.
Exit code: 0 = healthy, 1 = unhealthy.
Useful for cron monitoring scripts.

Usage:
    python3 check_relay.py
    python3 check_relay.py --port 8847   # force specific port
"""
import argparse
import json
import urllib.request
import urllib.error
import subprocess
import sys
import re


def detect_port():
    """Find Flask relay port by inspecting listening sockets."""
    try:
        result = subprocess.run(
            ["ss", "-tlnp"],
            capture_output=True, text=True, timeout=5
        )
        # Match lines with python process listening on localhost
        for line in result.stdout.splitlines():
            if "python" in line and "server.py" in line:
                m = re.search(r'127\.0\.0\.1:(\d+)', line)
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

    port = args.port or detect_port()
    if not port:
        # Fallback: try common ports
        for p in [8847, 8848]:
            if check_health(p):
                return 0
        print("NO_RELAY_FOUND | no python server.py process listening on common ports")
        sys.exit(1)

    if check_health(port):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
