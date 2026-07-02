# Session Changelog

Accumulated changes to the lightnovel-tracker skill across sessions.
This file absorbs the session-specific "Updates made" blocks from SKILL.md
so the main skill document stays lean and class-level.

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

- **Added Chinese numeral volume detection** to `scripts/parse_and_report.py`: `CN_NUMERALS` constant and `\s([一二三四五六七八九十])$` regex.
- **Added 3 new series to KNOWN_AUTHORS**: `少女述其罪有应得` (門倉), `美澄真白的正当杀人` (美澄真白), `义妹生活 another days` (三河ごーすと).
- **Updated `references/title-parsing.md`** with Chinese numeral detection patterns.
- **New pitfalls**: Simplified/Traditional mismatch in KNOWN_AUTHORS keys; double-escaped regex in script files.
