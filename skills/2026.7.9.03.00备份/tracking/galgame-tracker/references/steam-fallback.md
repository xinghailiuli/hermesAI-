# Steam Fallback — Chinese-Original VN Descriptions

## Reality check

Steam fallback for Chinese-original VNDB entries **almost never succeeds**. In the July 2026 cron run, 0 out of 3 Chinese-original games (染上你的颜色, 伊利斯之梦, 寻味记) were found on Steam. All timed out or returned no results.

Most Chinese-original VNs are distributed via DLSite, FANZA, or other non-Steam platforms. Steam is dominated by English-language VNs and Japanese eroge with translation patches.

## When to attempt

Only for the top 1-2 Chinese-original games if they have prominent Chinese names. Allocate at most 30 seconds per lookup (timeout issues). Do not treat empty results as notable — just use "（暂无简介）".

## Known issue

Even when Steam is reachable, the `game_description_snippet` div may not exist on the store page (especially for free/tiny indie titles). The `application/ld+json` script tag is more reliable but also often absent for very small developers.

## Recommendation

Skip Steam fallback entirely in cron mode unless manual inspection confirms the game is definitely on Steam.
