# Author Research: Identifying Unknown Items-Array Authors

Items-array entries lack `[author]` brackets. When both `extract_author()` and the `known-series-authors` lookup return `None`, use the following fallback strategies.

## 1. Ranks cross-reference

Check if the same `aid` appears in the ranks array. Ranks entries always carry `[author]` brackets and explicit timestamps. If the aid matches, use the ranks author.

## 2. Title-pattern heuristics

In category 3/106 (日轻/韩轻 translation section), titles without brackets are almost always JP/KR translations, not Chinese web novels.

**JP cultural keywords** (strongly suggest 日轻):
- 江户/江戸 (Edo period — unmistakably JP)
- 花魁 (Oiran — JP courtesan culture)
- 暗部/闇部 (dark side/organization — common in JP urban fantasy)
- 異世界 / 异世界 (another world — ubiquitous JP isekai genre)
- 魔王/勇者/聖女/賢者 (demon lord/hero/saint/sage — typical JP fantasy tropes)
- 学園/學園 (school setting)
- 刀剣/刀劍/太刀 (Japanese swords)
- 神社/巫女 (shrine/shrine maiden)
- 退魔/祓魔 (exorcism — JP fantasy)

**CN web novel markers** (rarely seen in category 3/106, but if present — likely CN):
- 系统流 (system novel), 穿越 (time travel — though also used in JP isekai)
- 赘婿, 龙王, 神医 (cliché CN web novel archetypes)
- Author name is a Chinese-style pen name without kana

## 3. External knowledge application

If you recognize the series from prior knowledge:

| Series | Author | Notes |
|--------|--------|-------|
| 暗部共生少女 | 鎌池和馬 | Toaru series spinoff, features "Dark Side" organizations |
| 取代江户花魁后，我决定登上花街之巅 | 葉月十一 | 「江戸の花魁を継いだら、花街の頂点に君臨することにしました」 |

**Always update both files when you discover a new author**:
- `references/known-series-authors.md` — the human-readable lookup table
- `scripts/parse_and_report.py` — the `KNOWN_AUTHORS` dict in the script

If you cannot determine the author, report as "未知" and let the next session with older ranks data fill it in.

### ⚠️ Bracket-content caveat: translator name vs author name

Rank entries carry `[bracket content]` in their title, but the bracket may contain the **translator's name** rather than the original author. Observed case:
- `[夜凪] 森林边上的小小魔女` — "夜凪" is the translator; original author is 小石川うみ

The `extract_author()` function is a naive bracket-grabber and cannot distinguish translator from author. When you *recognize* a series and the bracket text doesn't match the known author, do NOT trust the bracket text for that entry. Record the discrepancy in changelog.

When adding a series to `known-series-authors.md` that was only seen via a translator bracket, note this in the "Notes" column so future sessions know why the bracket author differs from the true author.

## 4. Cross-session enrichment

Items entries eventually migrate to the ranks array over ~7+ days. A future cron session will likely resolve today's "未知" entries naturally. Monitor repeated "未知" entries across sessions — if the same series keeps appearing in items without ranks migration, add it to known-series-authors.md manually.
