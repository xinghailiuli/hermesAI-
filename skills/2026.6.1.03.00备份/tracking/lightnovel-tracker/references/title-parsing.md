# Title Parsing: Author & Volume Extraction

The NUXT state titles carry author and volume info embedded in the string.
Parsing them systematically avoids manual inspection of each entry.

## Author Extraction

Authors appear in square brackets `[作者名]` at the beginning of the title:

```python
def extract_author(title: str) -> str:
    m = re.search(r'\[([^\]]+)\]', title)
    return m.group(1) if m else '未知'
```

Japanese authors (日轻) typically have:
- Kanji names (西条阳, 鏡遊, 夜方 宵)
- Kana-mixed names (白井ムク, としぞう)
- Romaji/kana combinations (レオナールD)

Korean authors (韩轻) typically have Hangul: `[최지인]`

Chinese web novel authors (国产网文) rarely use the `[author]` bracket convention
in category 3/106 — they appear more often in different categories. When brackets
are present on CN works, the name is typically a Chinese pen name.

**JP vs CN disambiguation heuristic:**
- Has kana (hiragana/katakana `[ァ-ヶぁ-ゔー]`): definitely 日轻
- Has Hangul (`[가-힣]`): definitely 韩轻
- Pure kanji in brackets, no kana: check series name against known JP works;
  in category 3/106, bracket-authors are almost always JP translations

## Volume Extraction

Volume/chapter info appears in the title text (after removing the author bracket).
Patterns and their extraction priority:

```python
def extract_volume(title: str) -> str:
    # Strip author bracket first
    clean = re.sub(r'\[.*?\]', '', title).strip()

    patterns = [
        # Explicit volume markers
        (r'第(\d+)卷',           '第{0}卷'),
        (r'(\d+)\s*卷',          '{0}卷'),
        # Chapter markers
        (r'至第(\d+)话',         '至第{0}话'),
        (r'更新至第(\d+)话',     '至第{0}话'),
        (r'第(\d+)话',           '第{0}话'),
        # Status markers (parenthesized)
        (r'[（(](上|下)[）)]',   '{0}'),
        (r'[（(](全|完|已完结)[）)]', '已完结'),
        # Trailing number as volume (heuristic: < 50)
        (r'(\d+)$',              None),  # special handling
    ]

    for pat, fmt in patterns:
        m = re.search(pat, clean)
        if m:
            if fmt is None:
                n = int(m.group(1))
                if n < 50:
                    return f'第{n}卷'
            else:
                return fmt.format(*m.groups())

    return '—'
```

### Examples

| Title | Author | Volume |
|-------|--------|--------|
| `[白井ムク] 风纪委员的羞耻游戏 第一卷` | 白井ムク | 第1卷 |
| `义妹生活 12` | 三河ごーすと (known) | 第12卷 |
| `[冷凍食品]負債兩千萬... (5/28 第三話完)` | 冷凍食品 | 已完结 |
| `[としぞう]同为败犬...[更新至第二话]` | としぞう | 至第2话 |
| `[鏡遊]御姐派的我，为何会喜欢上萝莉的你？` | 鏡遊 | — |
| `重生之後與前世戀人...※可是好感度為0 1` | 未知 | 第1卷 |

### Items-array entries (no author brackets)

Items titles lack `[author]` brackets. Author is always `未知` unless
cross-referenced with a ranks entry sharing the same `aid`. Volume extraction
still works on the title text.
