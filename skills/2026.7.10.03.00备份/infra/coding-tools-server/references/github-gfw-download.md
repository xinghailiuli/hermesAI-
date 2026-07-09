# Downloading GitHub Release Assets from Behind GFW

When downloading release assets (APKs, binaries, tools) from GitHub on a Chinese
server behind the GFW, standard `curl` or `wget` may fail due to:
- TLS handshake failures through mihomo/Clash proxies
- GitHub redirects to CDN domains that are also blocked
- GnuTLS + proxy compatibility issues

## Preferred Method: ghproxy.net Mirror

Use `ghproxy.net` as a China-accelerated CDN mirror:

```bash
curl -L "https://ghproxy.net/https://github.com/{owner}/{repo}/releases/download/{tag}/{filename}" -o output
```

## Best for Large Files: aria2c Multi-Threaded

```bash
aria2c -x 8 -s 8 -k 1M \
  --max-tries=5 --connect-timeout=15 --timeout=120 \
  --continue=true -d /tmp -o output.file \
  "https://ghproxy.net/https://github.com/{owner}/{repo}/releases/download/{tag}/{filename}"
```

Key flags:
- `-x 8`: 8 connections per server
- `-s 8`: 8 split points (segment count)
- `-k 1M`: 1 MiB per segment
- `--continue=true`: resume on interruption
- `--max-tries=5`: retry up to 5 times

## Direct CDN URL Method (via proxy)

If `ghproxy.net` is down, get the raw Azure CDN URL through the proxy:

```bash
proxy="http://127.0.0.1:7897"
cdn_url=$(curl -sI -x "$proxy" \
  "https://github.com/{owner}/{repo}/releases/download/{tag}/{file}" \
  -H "User-Agent: Mozilla/5.0" 2>&1 | grep -i "^location:" | sed 's/^[Ll]ocation: //')

# Download directly from Azure CDN (need --url to handle special chars)
curl -L --url "$cdn_url" -o output
```

## Verification

Always verify downloaded files:

```bash
# Check file type
file /tmp/downloaded.apk  # Should say "Android package (APK)" or expected type
# Check ZIP structure (APKs, JARs, etc.)
unzip -l /tmp/downloaded.apk | head -10
# Verify file size matches release metadata
ls -lh /tmp/downloaded.apk
```

## Pitfalls

- **GitHub redirects break behind GFW**: The initial `github.com` URL redirects to `release-assets.githubusercontent.com` (Azure CDN), which is also blocked. `ghproxy.net` handles this redirect chain.
- **mihomo/Clash SNI masking**: Many VMess proxies use `servername: gw.alicdn.com` which clashes with GitHub's CDN. The connection connects at TCP level but TLS fails.
- **GnuTLS + mihomo incompatibility**: Git's GnuTLS backend fails with `gnutls_handshake() failed: The TLS connection was non-properly terminated` through mihomo proxy. Use SSH protocol + SOCKS5 proxy (`GIT_SSH_COMMAND`) or direct connection.
- **No progress feedback**: `curl -L` through proxy for large files may appear to hang. Use `aria2c` for progress bars.
- **Rate limits**: GitHub API has 60 req/h for unauthenticated users. Download rate limits are per-IP.
