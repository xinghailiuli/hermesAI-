# Session Changelog

Accumulated changes to the lightnovel-tracker skill across sessions.
This file absorbs the session-specific "Updates made" blocks from SKILL.md
so the main skill document stays lean and class-level.

## 2026-07-06 — PARAMS extended to 'az'; NUXT param count fragility documented

- Script crashed with `ValueError: invalid literal for int() with base 10: 'ak'`
  when `rank:b,aid:ak,...` could not resolve param reference 'ak'.
- Root cause: `PARAMS` list only went up to 'ag' (48 params) but SSR now has
  67 params (need 'am' — extended to 'az' for headroom).
- Fixed in `scripts/parse_and_report.py` and `SKILL.md`.
- Added pitfall note about param count drift in SKILL.md.
- First report this session: only 1 new entry (天空的彼端 02, unknown author).

## 2026-07-05 session

- **Added CN web novel filtering** to `scripts/parse_and_report.py`: new `is_cn_series()` function with `CN_SERIES_MARKERS` regex list, `CN_BRACKET_AUTHORS` set, and numbered-chapter heuristics. Active filtering of 国产网文 before they enter the categorized output.
- **Added `series_name` extraction** from ranks entries: needed for CN filtering (the `[web自翻]` marker lives in `series_name`). Introduced param-reference resolution for `series_name` values.
- **Added `week_older` section** (📊 `${near_days}~${week_days}天前`) to the report output — previously this data was silently discarded. Now the 5-7 day window is shown when non-empty.
- **Added `🔇` section** when only CN entries were found in the target window — prevents confusing silence when the only entries were filtered.
- **Added author mapping**: `乱世千金倪亚・利斯顿 → 南野海風` to `scripts/parse_and_report.py` KNOWN_AUTHORS dict.
- **Reorganized KNOWN_AUTHORS** alphabetically for maintainability.
- **Updated SKILL.md** with dedicated CN web novel filtering section (Step 3 filtering subsection + canonical `is_cn_series()` code block) and new pitfalls entry for CN novels in category 3/106.

## 2026-07-01 session

- **Added author mapping**: `森林边上的小小魔女 → 小石川うみ` (森のほとりの小さな魔女) to both `scripts/parse_and_report.py` KNOWN_AUTHORS dict and `references/known-series-authors.md`.
- **Fixed dual-source-of-truth problem** in `references/known-series-authors.md`: replaced the inline Python snippet (which was desynced from the actual script) with a single-source-of-truth note pointing to `scripts/parse_and_report.py`.
- **Extracted session changelogs** from SKILL.md into this file — the main SKILL.md should stay class-level, not accumulate session-by-session narratives.

## 2026-06-30 session

- **Fixed section-end detection** in `scripts/parse_and_report.py`: replaced fragile `data_obj.find('},{', ln_idx)` with bracket-depth tracking.
- **Fixed items array extraction**: added proper bracket-depth tracking for the `items:[...]` array boundary.
- **New pitfall**: CDN timestamp clock skew ~24h into the future — documented mitigation.
- **Structural confirmation**: items array extraction via split-on-`{id:` within `items_raw` continues to work when section-end and array-boundary detection are sound.

## 2026-06-29 session

- **Added author mapping**: `农林 → 白鳥士郎`.
- **New pitfall**: Section boundary `},{` fragility — `data_obj.find('},{', ln_idx)` can match items-array separators instead of the true category boundary.

## 2026-06-28 session

- **Added Chinese numeral volume detection** to `scripts/parse_and_report.py`: `CN_NUMERALS` constant and `\\s([一二三四五六七八九十])$` regex.
- **Added 3 new series to KNOWN_AUTHORS**: `少女述其罪有应得` (門倉), `美澄真白的正当杀人` (美澄真白), `义妹生活 another days` (三河ごーすと).
- **Updated `references/title-parsing.md`** with Chinese numeral detection patterns.
- **New pitfalls**: Simplified/Traditional mismatch in KNOWN_AUTHORS keys; double-escaped regex in script files.
