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
    '冬季限定夾心巧克力事件': '米澤穂信',
    '夏季限定熱帶水果聖代事件': '米澤穂信',
    '秋季限定栗金飩事件': '米澤穂信',
    '春季限定草莓塔事件': '米澤穂信',
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
