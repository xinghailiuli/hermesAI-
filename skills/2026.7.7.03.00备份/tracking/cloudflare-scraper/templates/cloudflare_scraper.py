"""
Cloudflare Bypass Scraper for Comic/Manga Sites
================================================
Uses curl_cffi's TLS fingerprint spoofing to bypass Cloudflare protection.

Usage:
  python3 cloudflare_scraper.py <album_id>

Config:
  - PROXY_URL: Set proxy for blocked sites (e.g. "http://127.0.0.1:7897")
  - BROWSER_VERSION: Chrome/Firefox version to impersonate
  - TARGET_DOMAIN: Which site to scrape (nhentai, 18comic, etc.)
"""

import sys
from curl_cffi import requests

# ==================== Configuration ====================
PROXY_URL = "http://127.0.0.1:7897"   # None for direct connection
BROWSER_VERSION = "chrome120"          # chrome110, firefox120, safari17_0
TARGET_DOMAIN = "nhentai.net"          # or 18comic.vip, etc.
# =======================================================


def fetch_album_data(album_id: str):
    target_url = f"https://{TARGET_DOMAIN}/g/{album_id}/"
    proxies = {"http": PROXY_URL, "https": PROXY_URL} if PROXY_URL else None

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;"
                  "q=0.9,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    print(f"🔄 Fetching [{album_id}] from {TARGET_DOMAIN} ...")
    print(f"   Proxy: {proxies}")
    print(f"   Impersonate: {BROWSER_VERSION}")

    try:
        response = requests.get(
            target_url,
            headers=headers,
            proxies=proxies,
            impersonate=BROWSER_VERSION,
            timeout=15
        )

        if response.status_code == 200:
            print("✅ Page retrieved!")
            print(response.text[:300])
            return True
        elif response.status_code == 404:
            print(f"❌ 404 — ID {album_id} does not exist on {TARGET_DOMAIN}")
            return False
        elif response.status_code in (403, 503):
            print(f"⚠️ Still blocked by Cloudflare ({response.status_code})")
            print("💡 Try: different proxy, different BROWSER_VERSION, or direct API access")
            return False
        else:
            print(f"❓ Unknown status: {response.status_code}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"🚨 Connection failed: {e}")
        print("💡 Check: proxy address/port, node availability, or try without proxy")
        return False


if __name__ == "__main__":
    album_id = sys.argv[1] if len(sys.argv) > 1 else "356448"
    fetch_album_data(album_id)
