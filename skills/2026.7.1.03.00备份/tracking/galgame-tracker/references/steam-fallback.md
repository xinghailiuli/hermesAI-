# Steam Description Fallback for VNDB Cron Reports

When VNDB returns `null` descriptions for Chinese-original games, supplement from Steam.

## Technique

### Step 1: Find Steam App ID

```bash
# URL-encode the Chinese title, search Steam
app_id=$(curl -s --connect-timeout 10 --max-time 15 \
  "https://store.steampowered.com/search/?term=$(python3 -c 'import urllib.parse; print(urllib.parse.quote(sys.argv[1]))' "中文标题")" \
  2>/dev/null | grep -oP 'app/\d+' | head -1)
```

### Step 2: Extract description snippet

```bash
curl -s --connect-timeout 10 --max-time 15 \
  "https://store.steampowered.com/app/$app_id" 2>/dev/null | python3 -c "
import sys, re
html = sys.stdin.read()
match = re.search(r'class=\"game_description_snippet\"[^>]*>(.*?)</div>', html, re.DOTALL)
if match:
    text = re.sub(r'<[^>]+>', '', match.group(1)).strip()
    print(text)
"
```

### Step 3: Use directly in report

If Steam returns Chinese text, use it verbatim as the game description.
If Steam returns English text, use it cleaned of HTML tags.

## Constraints

- Rate limit: max 3-5 Steam lookups per cron run.
- Prefer VNDB descriptions first; only supplement the top 2-3 Chinese-original entries missing VNDB descriptions.
- If Steam search returns no app ID or no snippet, skip gracefully — use "（暂无简介）".
- Steam pages can be ~200KB+ HTML; use short timeouts (10-15s).
