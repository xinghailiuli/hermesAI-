# Known Series → Author Mapping

Items-array entries lack `[author]` brackets. This lookup enriches reports
with known author names for popular series that recur across sessions.
Add new entries when a series appears in items and its author is confirmed
(via ranks cross-reference, manual verification, or prior knowledge).

Format: key = distinctive title substring (lowercase, no spaces), value = author name

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
| 暗部共生少女 | 鎌池和馬 | Kamachi Kazuma, Toaru series spinoff about "Dark Side" organizations |
| 取代江户花魁后，我决定登上花街之巅 | 葉月十一 | Hazuki Juuichi, 「江戸の花魁を継いだら、花街の頂点に君臨することにしました」 |
| 受难的不吉波普 / 不吉波普 | 上遠野浩平 | Kouhei Kadono, Boogiepop series |
| 少女述其罪有应得 | 門倉 | 日轻, 少女は罪を語るべき, 1卷完结 |
| 美澄真白的正当杀人 | 美澄真白 | 日轻, 美澄真白の正当殺人, 1卷完结 |
| 义妹生活 another days | 三河ごーすと | Mikawa Ghost, 义妹生活 spin-off/side stories |

## Python helper

```python
KNOWN_AUTHORS = {
    '在異世界獲得超強能力的我': '美紅',
    '佐佐木與文鳥小嗶': 'ぶんころり',
    '雖然現在還只是': '南野海風',  # fuzzy prefix match
    '義妹生活': '三河ごーすと',
    '劍鬼轉生': 'クレハ',
    '浮游学园的爱丽丝&雪莉': 'むらさきゆきや',
    'Sword Art Online': '川原礫',
    '刀劍神域': '川原礫',
    '不吉波普': '上遠野浩平',
    '冬季限定夾心巧克力事件': '米澤穂信',
    '夏季限定熱帶水果聖代事件': '米澤穂信',
    '秋季限定栗金飩事件': '米澤穂信',
    '春季限定草莓塔事件': '米澤穂信',
    '彈珠汽水瓶裡的千歲同學': '裕夢',
    '暗部共生少女': '鎌池和馬',
    '取代江户花魁': '葉月十一',
    '少女述其罪有应得': '門倉',  # also 少女述其罪有應得 (Trad)
    '美澄真白的正当杀人': '美澄真白',
    '义妹生活 another days': '三河ごーすと',
}

def lookup_author(title: str) -> str | None:
    for key, author in KNOWN_AUTHORS.items():
        if key in title:
            return author
    return None
```

Use this after `extract_author()` fails — only when the standard bracket
extraction returns `None`. The lookup should NOT override bracket-extracted
authors (those are always authoritative).
