# CDN Timestamps & Item Dating

Discovered 2026-05-29: the `items` array entries lack explicit `time` fields, but
their `pic_url` query string contains a Unix epoch timestamp that serves as a
reliable proxy for the article publish date.

## How It Works

Each item in the `items` array has a `pic_url` like:

```
https://res.lightnovel.fun/recom/ee526e2f2937b93300d5f0ed90d752c9.jpg?m=-1SXrLzp6Ku6iYQ2C2p0Qg&t=1779877918
```

The `t=` parameter is a **Unix epoch second** — the time the cover image was
uploaded to the CDN. This closely approximates the article publish time.

### Extraction

```python
import re
from datetime import datetime

t_match = re.search(r'[?&]t=(\d+)', pic_url)
if t_match:
    ts = int(t_match.group(1))
    if 1_000_000_000 < ts < 2_000_000_000:
        # Valid Unix epoch (2001-09-09 through 2033-05-18)
        cdn_date = datetime.fromtimestamp(ts)
```

### Placeholder Detection

Some `pic_url` values use static/placeholder timestamps — typically `t=8000000000`
(2223-07-06). These are **not** real dates. Discard any timestamp outside the
1e9–2e9 range.

## Items vs Ranks: Field Comparison

| Field | ranks array | items array |
|-------|-------------|-------------|
| `time` (publish date) | ✅ explicit `YYYY-MM-DD HH:MM:SS` | ❌ absent |
| `title` | ✅ with `[author]` bracket | ✅ title only, no author |
| Author name | ✅ in title bracket `[西条阳]` | ❌ no author field |
| `aid` (article ID) | ✅ numeric | ✅ via `action_params` |
| `pic_url` / cover | ✅ `t=` often placeholder (`8000000000`) | ✅ `t=` is real Unix epoch |
| `hits`, `comments` | ✅ | ✅ |
| `series_name` | ✅ for multi-volume | ❌ absent |
| Recency | ⚠️ stale (7+ day lag observed) | ⚠️ mixed: CDN timestamps accurate but array is cumulative — entries persist across sessions; always validate per-item |

**Strategy**: Extract and merge both arrays. Use `ranks` for rich metadata
(author, description, series name). Use `items` for fresh content
(recent uploads) — but validate every item's CDN timestamp; the array is
cumulative and may contain stale entries from previous sessions. Cross-reference
by `aid` to enrich items with rank metadata when items graduate to ranks.

## Aid-to-Date Linear Correlation

Observed aid increments from the 2026-05-29 session:

| Date | Aid | Δ aid | Δ days | aids/day |
|------|-----|-------|--------|----------|
| 03-05 | 1143589 | — | — | — |
| 03-31 | 1143955 | +366 | 26 | 14.1 |
| 04-02 | 1143992 | +37 | 2 | 18.5 |
| 04-22 | 1144255 | +263 | 20 | 13.2 |
| 04-27 | 1144301 | +46 | 5 | 9.2 |
| 05-05 | 1144366 | +65 | 8 | 8.1 |
| 05-12 | 1144435 | +69 | 7 | 9.9 |
| 05-14 | 1144464 | +29 | 2 | 14.5 |
| 05-18 | 1144503 | +39 | 4 | 9.8 |
| 05-22 | 1144535 | +32 | 4 | 8.0 |

**2026-05-29 session data point**:
| 05-29 | 1144626 | +91 | 7 | 13.0 |

**2026-06-01 session data point**:
| 06-01 | 1144626 | +0 | 3 | 0.0 |

**2026-06-02 session data point**:
| 06-02 | 1144626 | +0 | 1 | 0.0 |

Note: 0 aids/day over June 1 weekend is anomalous — the site SSR may not have
refreshed over the weekend. The ranks array did update (new entry aid=1144626
with explicit time 2026-05-29, which was absent on 05-29), but no new aids
beyond 1144626 appeared in either array.

The 06-02 session confirmed: max aid still 1144626 (ranks, May 29). However,
the items array gained a new entry aid=1144598 with CDN timestamp 2026-06-02
(lower aid number, later date) — the items array received a fresh entry while
ranks remained static. This reinforces that the items array is the source of
newest content, NOT ranks.

**Recent average**: ~8–14 aids/day (excluding anomalous 0-day periods).
Use `10 aids/day` as a rough heuristic when CDN timestamps are unavailable.

### Estimation formula

```python
estimated_date = last_confirmed_date + timedelta(days=(aid - last_confirmed_aid) / 10)
```

## Verified Session (2026-05-29)

Three items detected within a 3-day window (May 26–29) using CDN timestamps:

| aid | title | CDN timestamp | 
|-----|-------|---------------|
| 1144578 | 义妹生活 12 | 2026-05-27 18:33:54 |
| 1144581 | 難得拿到外掛轉生至異世界...6 | 2026-05-27 18:33:02 |
| 1144582 | 劍鬼轉生 以究極之劍斬裂魔術 1 | 2026-05-27 18:31:58 |

All three were in the `items` array only — the `ranks` array had stopped at
aid=1144535 (2026-05-22). Without the CDN timestamp technique, these three
entries would have been missed.

## Items Array Persistence Across Sessions

**Key finding (2026-06-01)**: The SSR `items` array is cumulative — entries are
NOT removed between sessions. The same items from 2026-05-29 were still present
in the items array on 2026-06-01, now 5 days old. Implication:

- You CANNOT assume all items entries are recent. CDN timestamp validation is mandatory.
- Items do migrate to the `ranks` array over time (observed: aid=1144581 appeared
  in items on 05-29, then in ranks on 06-01), but the items array still retains them.
- During slow periods (weekends, holidays), the items array may contain only
  stale entries with no new content in the target window.

**Session comparison (05-29 → 06-01)**:

| aid | 2026-05-29 location | 2026-06-01 location | Δ |
|-----|---------------------|---------------------|---|
| 1144578 | items (CDN: 05-27) | items (CDN: 05-27) | unchanged |
| 1144581 | items (CDN: 05-27) | ranks (time: 05-25) | migrated |
| 1144582 | items (CDN: 05-27) | items (CDN: 05-27) | unchanged |
| 1144626 | — (not present) | ranks (time: 05-29) | new in ranks |
