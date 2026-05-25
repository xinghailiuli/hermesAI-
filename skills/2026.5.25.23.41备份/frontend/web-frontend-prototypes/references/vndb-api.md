# VNDB API Reference

## Query Pattern

POST to `https://api.vndb.org/kana/vn` with JSON body:

```json
{
  "filters": ["search", "=", "Exact Game Title"],
  "fields": "id,title,image.url,image.id,screenshots.url",
  "results": 3
}
```

## Key Facts

- **VN ID ≠ Cover Image ID.** A game with VN ID `v20424` might have cover `cv85430`. Never guess CV IDs from VN IDs.
- **Always read `image.url` directly** — don't construct URLs from IDs. The API returns the full CDN URL.
- **Cover URL format** (when constructing): `https://t.vndb.org/cv/{last_two}/{full_id}.jpg`
- **Screenshot field:** `screenshots.url` — returns array of screenshot CDN URLs when populated.
- **Rate limit:** ~0.3s between requests in `execute_code` loops. Use `time.sleep(0.3)`.
- **Download with:** `curl -sL --max-time 15 -o file.jpg -H "User-Agent: Mozilla/5.0" -H "Referer: https://vndb.org/" URL`
- **Verify after download:** `stat -c%s file.jpg` — files under 2KB are error pages (usually 146 bytes).
- **Some games not on VNDB:** Mobile gacha (Heaven Burns Red), action-RPG hybrids (Fate/Samurai Remnant), some doujin titles. Generate PIL placeholders or remove from catalog.

## Batch Search Example (Python)

```python
import json, urllib.request, time

games = [("ATRI", "ATRI -My Dear Moments-"), ("SP", "Summer Pockets")]
results = {}
for key, term in games:
    data = json.dumps({
        "filters": ["search", "=", term],
        "fields": "id,title,image.url,image.id",
        "results": 3
    }).encode()
    req = urllib.request.Request("https://api.vndb.org/kana/vn", data=data,
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        r = json.loads(resp.read())
        if r["results"]:
            vn = r["results"][0]
            results[key] = {"vn_id": vn["id"], "cover_url": vn["image"]["url"]}
    time.sleep(0.3)
```

## Screenshot Download

When `screenshots` field is populated, download for CG gallery:
```
curl -sL -o cg_screenshots/sp_cg1.jpg "https://t.vndb.org/sf/74/111674.jpg"
```

Screenshot URL format: `https://t.vndb.org/sf/{last_two}/{full_id}.jpg`

## Verified Cover IDs (2020-2025 notable games)

| Game | VN ID | Cover ID | Cover URL |
|------|-------|----------|-----------|
| ATRI | v27448 | cv76012 | cv/12/76012.jpg |
| Summer Pockets | v20424 | cv85430 | cv/30/85430.jpg |
| Sakura, Moyu | v22313 | cv79671 | cv/71/79671.jpg |
| Tsui no Stella | v29443 | cv75915 | cv/15/75915.jpg |
| LOOPERS | v29445 | cv75909 | cv/09/75909.jpg |
| Anonymous;Code | v17101 | cv75863 | cv/63/75863.jpg |
| Subahibi HD | v3144 | cv90017 | cv/17/90017.jpg |
| Aonatsu Line | v24702 | cv81645 | cv/45/81645.jpg |
| ONE. Remake | v51 | cv76154 | cv/54/76154.jpg |
| Tenshi Soudou | v40520 | cv88666 | cv/66/88666.jpg |
| Hoshizora Tetsudou | v28297 | cv92115 | cv/15/92115.jpg |
| PARQUET | v31807 | cv79891 | cv/91/79891.jpg |
| D.C.5 | v36687 | cv86612 | cv/12/86612.jpg |
| Hamidashi Totsu | v33205 | cv81091 | cv/91/81091.jpg |
| Sakura no Kumo | v26664 | cv90878 | cv/78/90878.jpg |
| Clover Day's | v13325 | cv94749 | cv/49/94749.jpg |
| Aokana | v12849 | cv79855 | cv/55/79855.jpg |
| Summer Pockets RB | (same as SP) | cv85447 | cv/47/85447.jpg |
| Senren Banka | v19073 | cv80746 | cv/46/80746.jpg |
| Sakura no Uta | v562 | cv79663 | cv/63/79663.jpg |
| Riddle Joker | v23936 | cv78086 | cv/86/78086.jpg |
| Cafe Stella | v27999 | cv86642 | cv/42/86642.jpg |
| Making Lovers | v21799 | cv78224 | cv/24/78224.jpg |
| Gin'iro Haruka | v19913 | cv77583 | cv/83/77583.jpg |
| Hakoniwa | — | cv83703 | cv/03/83703.jpg |
| Kinkoi (Golden Loveriche) | — | cv84122 | cv/22/84122.jpg |
| Sanoba Witch | — | cv64655 | cv/55/64655.jpg |
