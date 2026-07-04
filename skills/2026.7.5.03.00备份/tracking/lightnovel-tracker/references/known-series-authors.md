# Known Series → Author Mapping

Items-array entries lack `[author]` brackets. This lookup enriches reports
with known author names for popular series that recur across sessions.
Add new entries when a series appears in items and its author is confirmed
(via ranks cross-reference, manual verification, or prior knowledge).

Format: key = distinctive title substring, value = author name

## Confirmed mappings

| Series pattern | Author | Notes |
|---------------|--------|-------|
| 在異世界獲得超強能力的我 | 美紅 | 美紅 (Miku), long-running isekai |
| 佐佐木與文鳥小嗶 | ぶんころり | Bunkorori, MF文庫J |
| 雖然現在還只是「青梅竹馬的妹妹」 | 南野海風 | Confirmed via ranks in 2026-06-01 session |
| 義妹生活 | 三河ごーすと | Mikawa Ghost |
| 劍鬼轉生 | クレハ | Kureha |
| 浮游学园的爱丽丝&雪莉 | むらさきゆきや | Murasaki Yukiya (confirmed via ranks) |
| Sword Art Online / 刀劍神域 | 川原礫 | Kawahara Reki, includes Progressive, Unital Ring |
| 冬季限定夾心巧克力事件 | 米澤穂信 | Yonezawa Honobu, 小市民系列 (also 春季/夏季/秋季限定) |
| 彈珠汽水瓶裡的千歲同學 | 裕夢 | Hiromu, 千歳くんはラムネ瓶のなか, GAGAGA文庫 |
| 暗部共生少女 | 鎌池和馬 | Kamachi Kazuma, Toaru series spinoff |
| 取代江户花魁后，我决定登上花街之巅 | 葉月十一 | Hazuki Juuichi |
| 受难的不吉波普 / 不吉波普 | 上遠野浩平 | Kouhei Kadono, Boogiepop series |
| 少女述其罪有应得 | 門倉 | 日轻, 少女は罪を語るべき, 1卷完结 |
| 美澄真白的正当杀人 | 美澄真白 | 日轻, 美澄真白の正当殺人, 1卷完结 |
| 义妹生活 another days | 三河ごーすと | Mikawa Ghost, 义妹生活 spin-off/side stories |
| 农林 | 白鳥士郎 | 白鳥士郎 (Shiratori Shirou), Nourin series, GA文庫. Added 2026-06-29. |
| 森林边上的小小魔女 | 小石川うみ | 日轻, 森のほとりの小さな魔女 (Little Witch by the Forest). Added 2026-07-01. |

## Python helper (single source of truth)

**The canonical `KNOWN_AUTHORS` dict lives in `scripts/parse_and_report.py`** — that file is the live code used by the cron job and is always authoritative. The table above documents the mappings for human readers.

Always update `scripts/parse_and_report.py` first when adding a new entry. The reference table is secondary documentation and may lag behind.

The lookup function in `parse_and_report.py`:

```python
def lookup_author(title):
    for key, author in KNOWN_AUTHORS.items():
        if key in title:
            return author
    return None
```

Use `lookup_author()` after `extract_author()` (bracket parse) returns `None`. The lookup should NOT override bracket-extracted authors — those are always authoritative.
