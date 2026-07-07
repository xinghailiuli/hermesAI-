#!/usr/bin/env python3
"""
Format fetched VNDB details into a Chinese-language Galgame report.
Reads a JSON array of VN objects from stdin, outputs markdown to stdout.

Usage: python3 format_report.py < /tmp/vndb_details.json > report.md
"""
from datetime import datetime
import json, re, sys

def truncate_text(text, max_len=350):
    """Truncate text safely — CJK-safe (don't split on spaces for Chinese text)."""
    if len(text) <= max_len:
        return text
    cjk_count = sum(1 for c in text[:max_len] if '\u4e00' <= c <= '\u9fff')
    if cjk_count > max_len * 0.3:
        return text[:max_len].rstrip() + '……'
    else:
        return text[:max_len].rsplit(' ', 1)[0] + '……'

def clean_desc(desc):
    """Remove BBCode/markup from VNDB descriptions. Handles [url=...], quote/quote, and stray brackets."""
    if not desc:
        return ''
    desc = re.sub(r'\[url=[^\]]+\]', '', desc)
    desc = desc.replace('[/url]', '')
    desc = re.sub(r'\[/?[^\]]*\]', '', desc)
    # Strip quote and /quote tags that appear in some descriptions
    desc = desc.replace('quote', '').replace('/quote', '')
    desc = ' '.join(desc.split())
    return desc.strip()

def get_cn_title(vn):
    """Extract Chinese title from titles array. Checks zh-Hans > zh-Hant > zh."""
    for t in vn.get('titles', []):
        if t['lang'] in ('zh-Hans', 'zh-Hant', 'zh'):
            return t['title']
    return None

def platform_icons(platforms):
    icon_map = {'win': 'Windows', 'lin': 'Linux', 'mac': 'Mac', 'and': 'Android', 'web': 'Web', 'swi': 'Switch', 'sw2': 'Switch 2', 'ps5': 'PlayStation 5'}
    return ' / '.join(icon_map.get(p, p) for p in platforms) if platforms else '未知'

def lang_flags(langs):
    """Build language flag + name display string."""
    flag_map = {
        'zh-Hans': '简体中文', 'zh-Hant': '繁体中文', 'en': '英语',
        'ja': '日语', 'ko': '韩语', 'es': '西班牙语', 'fr': '法语', 'de': '德语',
        'it': '意大利语', 'ru': '俄语', 'pt-br': '葡萄牙语(巴西)',
        'id': '印尼语', 'vi': '越南语', 'nl': '荷兰语', 'pl': '波兰语',
        'tr': '土耳其语', 'uk': '乌克兰语', 'pt-pt': '葡萄牙语'
    }
    return ' · '.join(flag_map.get(l, l) for l in langs)


data = json.load(sys.stdin)

# Priority ordering: Chinese originals > Chinese-supported > English-only
def sort_key(vn):
    langs = vn.get('languages', [])
    if langs and all(l in ('zh-Hans', 'zh-Hant', 'zh') for l in langs):
        return (0, -1 * (vn.get('rating') or 0))
    if 'zh-Hans' in langs or 'zh-Hant' in langs or 'zh' in langs:
        return (1, -1 * (vn.get('rating') or 0))
    return (2, -1 * (vn.get('rating') or 0))

sorted_vns = sorted(data, key=sort_key)

# Generate report with dynamic date
now = datetime.now()
year_str = now.strftime('%Y')
month_str = now.strftime('%m')
date_str = now.strftime('%Y-%m-%d')

print(f"# 🎮 Galgame 新作情报（{year_str}年{month_str}月）")
print()
print(f"> 抓取时间：{date_str} ｜ 数据来源：VNDB API ｜ 本期收录 {min(len(sorted_vns), 8)} 款新作")
print()

for i, vn in enumerate(sorted_vns[:8], 1):
    cn_title = get_cn_title(vn)
    en_title = vn.get('title', '')

    if cn_title and cn_title != en_title:
        name_line = f"## {i}. {cn_title}（{en_title}）"
    elif cn_title:
        name_line = f"## {i}. {cn_title}"
    else:
        name_line = f"## {i}. {en_title}"

    released = vn.get('released', '未知')
    devs = ', '.join(d['name'] for d in vn.get('developers', [])) if vn.get('developers') else '未知'
    platforms_str = platform_icons(vn.get('platforms', []))
    rating = vn.get('rating')
    rating_str = f"⭐ {rating:.1f}" if rating else "暂无评分"
    langs_str = lang_flags(vn.get('languages', []))
    img_url = vn.get('image', {}).get('url', '')
    sexual = vn.get('image', {}).get('sexual', 0)

    desc = clean_desc(vn.get('description', ''))
    if not desc:
        desc = '（暂无简介）'
    else:
        desc = truncate_text(desc, 350)

    nsfw_tag = " 🔞" if sexual > 1.0 else ""
    rating_badge = ""
    if rating:
        if rating >= 80:
            rating_badge = " 🏆高分推荐"
        elif rating >= 70:
            rating_badge = " ⭐值得关注"

    print(f"{name_line}{nsfw_tag}{rating_badge}")
    print(f"- **发售日**：{released}")
    print(f"- **开发商**：{devs}")
    print(f"- **平台**：{platforms_str}")
    print(f"- **评分**：{rating_str}")
    print(f"- **语言**：{langs_str}")
    print()
    print(f"> {desc}")
    print()
    if img_url:
        print(f"![封面]({img_url})")
    print()
    print("---")
    print()

# Summary
cn_support = sum(1 for vn in sorted_vns[:8]
                 if any(l in ('zh-Hans', 'zh-Hant', 'zh') for l in vn.get('languages', [])))
cn_only = sum(1 for vn in sorted_vns[:8]
              if vn.get('languages') and all(l in ('zh-Hans', 'zh-Hant', 'zh') for l in vn['languages']))
all_platforms = set()
for vn in sorted_vns[:8]:
    all_platforms.update(vn.get('platforms', []))
platform_names = {'win': 'Windows', 'lin': 'Linux', 'mac': 'Mac', 'and': 'Android', 'swi': 'Switch', 'web': 'Web', 'sw2': 'Switch 2', 'ps5': 'PlayStation 5'}

print("### 📊 本期小结")
print(f"- 共计收录 **{min(len(sorted_vns), 8)}** 款新作")
print(f"- **{cn_support}** 款支持中文（其中 **{cn_only}** 款为国产原创作品）")
print(f"- 涵盖平台：{' / '.join(platform_names.get(p, p) for p in sorted(all_platforms))}")
print()
print("---")
print("*数据来源于 VNDB API（vndb.org），部分游戏尚无中文简介。*")
