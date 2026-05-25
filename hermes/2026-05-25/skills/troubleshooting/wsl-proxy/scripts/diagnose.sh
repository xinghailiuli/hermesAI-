#!/bin/bash
# WSL → Windows proxy diagnostic script
# Usage: bash diagnose.sh [PORT]

PORT="${1:-7897}"

echo "=== WSL2 Proxy Diagnostic ==="
echo "Target port: $PORT"
echo ""

# 1. Internet test
echo "[1/4] Testing direct internet access..."
HTTP_CODE=$(curl -s --connect-timeout 5 -o /dev/null -w "%{http_code}" https://www.baidu.com 2>/dev/null)
if [ "$HTTP_CODE" = "200" ]; then
  echo "  ✓ Direct internet OK — proxy may not be needed"
else
  echo "  ✗ No direct internet (code: $HTTP_CODE)"
fi

# 2. Find Windows IPs
echo "[2/4] Finding Windows host IPs..."
GW_IP=$(ip route show default 2>/dev/null | awk '{print $3}')
NS_IP=$(grep nameserver /etc/resolv.conf 2>/dev/null | awk '{print $2}')
echo "  Gateway IP: ${GW_IP:-N/A}"
echo "  Nameserver IP: ${NS_IP:-N/A}"

# 3. Test proxy ports on various IPs
echo "[3/4] Testing proxy connectivity..."

test_proxy() {
  local ip=$1
  local port=$2
  local result=$(curl -x "http://${ip}:${port}" -s --connect-timeout 3 -o /dev/null -w "%{http_code}" https://github.com 2>/dev/null)
  if [ "$result" = "200" ] || [ "$result" = "301" ] || [ "$result" = "302" ]; then
    echo "  ✓ $ip:$port → HTTP $result"
    return 0
  else
    echo "  ✗ $ip:$port → $result"
    return 1
  fi
}

FOUND=false
for ip in 127.0.0.1 "$GW_IP" "$NS_IP"; do
  [ -z "$ip" ] && continue
  if test_proxy "$ip" "$PORT"; then
    FOUND=true
    break
  fi
done

# Also try common ports if specified port fails
if [ "$FOUND" = false ]; then
  echo "  Trying common proxy ports..."
  for p in 7890 10809; do
    if test_proxy "127.0.0.1" "$p"; then
      echo "  → Port $p works! Use this instead of $PORT."
      FOUND=true
      break
    fi
  done
fi

# 4. Summary
echo ""
echo "[4/4] Summary:"
if [ "$FOUND" = true ]; then
  echo "  ✓ Proxy reachable!"
else
  echo "  ✗ Proxy unreachable. Likely causes:"
  echo "    1. Windows Firewall blocking the port"
  echo "       Fix: New-NetFirewallRule -DisplayName 'Proxy' -Direction Inbound -Protocol TCP -LocalPort $PORT -Action Allow"
  echo "    2. Proxy not listening on 0.0.0.0 (Allow LAN disabled)"
  echo "    3. Wrong port — check proxy dashboard"
fi
