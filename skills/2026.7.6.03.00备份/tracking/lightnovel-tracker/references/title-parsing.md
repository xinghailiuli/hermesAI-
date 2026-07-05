# Title Parsing: Author & Volume Extraction

The NUXT state titles carry author and volume info embedded in the string.
Parsing them systematically avoids manual inspection of each entry.

## Author Extraction

Authors appear in square brackets `[作者名]` at the beginning of the title:

```python
def extract_author(title: str) -> str:
    m = re.search(r'\[([^\]]+)\]', title)
    return m.group(1) if m else None
```

**Important**: After extracting the author, strip the bracket from the display title to avoid duplication:

```python
def clean_title(title, author):
    """Remove author bracket from title for display"""
    t = re.sub(r'\[.*?\]\s*', '', title).strip()
    # Normalize excessive ideographic spaces
    t = re.sub(r'\u3000+', ' ', t)
    return t
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
CN_NUMERALS = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}

def extract_volume(title: str) -> str:
    # Strip author bracket first
    clean = re.sub(r'\[.*?\]', '', title).strip()

    patterns = [
        # Explicit volume markers
        (r'第(\d+)卷',           '第{0}卷'),
        # Chapter markers
        (r'至第(\d+)话',         '至第{0}话'),
        (r'第(\d+)话',           '第{0}话'),
        # Status markers (parenthesized)
        (r'[（(](上|下)[）)]',   '{0}'),
        (r'[（(](全|完|已完结)[）)]', '已完结'),
    ]

    for pat, fmt in patterns:
        m = re.search(pat, clean)
        if m:
            return fmt.format(*m.groups())

    # Number followed by space + text (mid-title): "书名 11 副标题"
    m = re.search(r'\s(\d+)\s', clean)
    if m:
        n = int(m.group(1))
        if 1 <= n < 50:
            return f'第{n}卷'

    # Number at end of title: "义妹生活 12"
    m = re.search(r'(\d+)$', clean)
    if m:
        n = int(m.group(1))
        if n < 50:
            return f'第{n}卷'

    # Bare number before closing punctuation: "爱丽丝&雪莉3)"
    m = re.search(r'[^\d](\d+)[)$）]', clean)
    if m:
        n = int(m.group(1))
        if 1 <= n < 50:
            return f'第{n}卷'

    # Chinese numeral at end of title: "花街之巅 三" = volume 3
    cn_match = re.search(r'\s([一二三四五六七八九十])$', clean)
    if cn_match:
        n = CN_NUMERALS.get(cn_match.group(1))
        if n:
            return f'第{n}卷（{cn_match.group(1)})'

    return '—'
```

### Examples

| Title | Author | Volume |
|-------|--------|--------|
| `[白井ムク] 风纪委员的羞耻游戏 第一卷` | 白井ムク | 第1卷 |
| `义妹生活 12` | 三河ごーすと (known) | 第12卷 |
| `佐佐木與文鳥小嗶 11 大冒險！來去異世界攻略迷宮` | ぶんころり | 第11卷 |
| `雖然現在還只是「青梅竹馬的妹妹」。 3 這是三年份的「謝謝」唷，學長。` | 未知 | 第3卷 |
| `人生逆轉 1 被劈腿又蒙受冤罪的我，受到學園第一美少女青睞` | 未知 | 第1卷 |
| `[冷凍食品]負債兩千萬... (5/28 第三話完)` | 冷凍食品 | 已完结 |
| `[としぞう]同为败犬...[更新至第二话]` | としぞう | 至第2话 |
| `[鏡遊]御姐派的我，为何会喜欢上萝莉的你？` | 鏡遊 | — |
| `浮游学园的爱丽丝&雪莉3` | 未知 | 第3卷 |
| `重生之後與前世戀人...※可是好感度為0 1` | 未知 | 第1卷 |
| `暗部共生少女 2` | 未知 (items) | 第2卷 |
| `取代江户花魁后，我决定登上花街之巅 三` | 葉月十一 (known) | 第3卷（三） |
| `义妹生活16` | 三河ごーすと (known) | 第16卷 |

### Volume number edge cases (from observed data)

- **Chinese numeral marker** `取代江户花魁后，我决定登上花街之巅 三` → detected as 第3卷 via `CN_NUMERALS` lookup and `\s([一二三四五六七八九十])$` regex. This pattern matches a space followed by a Chinese numeral at end of title.
- **No-space trailing numbers** `义妹生活16` has no space between title and volume number. The `(\d+)$` pattern handles this correctly.
- **Traditional → Simplified mismatch**: The SSR data uses Simplified Chinese for title text. When adding KNOWN_AUTHORS keys, use Simplified characters that match what the SSR actually emits, or add both variants.
