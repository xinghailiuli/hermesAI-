# Airport CDN Filtering: Deep Dive

Reproduction recipe from a real session where iwara.tv failed through mihomo proxy
while GitHub worked fine through the same nodes.

## Environment

- Server: Alibaba Cloud Hangzhou (47.108.235.219), Ubuntu 24.04
- Proxy: mihomo v1.19.3, 5 VMess nodes all using `servername: gw.alicdn.com`
- Target: iwara.tv (CDN resolves to 173.244.209.150 / 199.96.58.85)
- Result: `SSL_ERROR_SYSCALL` on every attempt

## Diagnostic trace

### Step 1: Confirm proxy works
```
curl --socks5 127.0.0.1:7897 https://github.com → 200 OK ✓
```

### Step 2: Test HTTPS through proxy
```
curl --socks5-hostname 127.0.0.1:7897 https://www.iwara.tv
→ SSL_ERROR_SYSCALL (exit 35)
```

### Step 3: Isolate TCP from TLS with HTTP
```
curl --socks5-hostname 127.0.0.1:7897 http://www.iwara.tv
→ GET / HTTP/1.1 sent successfully — TCP works, TLS is the problem
```

### Step 4: openssl s_client diagnostic
```
echo "Q" | openssl s_client -connect www.iwara.tv:443 \
  -proxy 127.0.0.1:7897 -servername www.iwara.tv -tls1_2
→ "SSL handshake has read 39 bytes and written 279 bytes"
→ "no peer certificate available"
→ "Cipher is (NONE)"
```

39 bytes read = TLS Alert from server/CDN rejecting the Client Hello.
279 bytes written = Client Hello sent successfully.
The CDN read our SNI=iwara.tv in the inner TLS and dropped the connection.

### Step 5: Confirm direct is blocked (baseline)
```
curl --noproxy '*' --connect-timeout 10 https://www.iwara.tv
→ TCP timeout (GFW blocks the IP)
```

### Step 6: Test all nodes
All 5 nodes (🇺🇸×2, 🇯🇵, 🇸🇬, 🇭🇰) — all use `servername: gw.alicdn.com` — all fail identically.

### Step 7: Attempt workaround — WebSocket transport
Adding `network: ws` to the VMess proxy config had no effect. The CDN inspects inner-TLS regardless of outer transport.

## Root Cause

Chinese airport providers use Alibaba CDN (`gw.alicdn.com`) as TLS fronting to bypass GFW.
This CDN has its own content filtering rules that block adult/gambling/niche sites based on
the SNI in the inner TLS Client Hello — even though the airport node itself would allow the traffic.

## Why the Same Nodes Work on Windows

The user's PC (Windows) uses SChannel as its TLS stack. SChannel sends different TLS Client
Hello (different cipher suites, extensions, fingerprint) than OpenSSL 3.0 on Linux. Some CDN
filters are triggered by Linux/OpenSSL fingerprints but not Windows/SChannel fingerprints.

## Workarounds (ranked by practicality)

1. **Local download** — Download on the user's PC and transfer via QQ
2. **Different airport** — One that doesn't front through Alibaba CDN (or without SNI-based content filtering)
3. **Different TLS stack** — Use GnuTLS, WolfSSL, or a custom cipher suite profile that doesn't trigger CDN filters
4. **Local Hermes deployment** — Run Hermes on the user's PC where the proxy works
