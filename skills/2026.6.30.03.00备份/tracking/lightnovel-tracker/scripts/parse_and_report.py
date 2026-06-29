#!/usr/bin/env python3
"""Parse lightnovel.fun SSR NUXT state and report recent JP/KR LN translations.

Usage:
    curl ... lightnovel.fun -o /tmp/ln_home.html
    python3 parse_and_report.py /tmp/ln_home.html [--days 3] [--near-days 5] [--week-days 7]
"""

import re
import sys
from datetime import datetime, timedelta, timezone

CST = timezone(timedelta(hours=8))
NOW = datetime.now(tz=CST)

# ── Known series → author lookup (items array has no author field) ──
KNOWN_AUTHORS = {
    '在異世界獲得超強能力的我': '美紅',
    '佐佐木與文鳥小嗶': 'ぶんころり',
    '雖然現在還只是': '南野海風',
    '義妹生活': '三河ごーすと',
    '义妹生活': '三河ごーすと',  # Simplified Chinese variant
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
    '农林': '白鳥士郎',  # Nourin/农林 by 白鳥士郎 (Shiratori Shirou)
}

# ── Param resolver ──
PARAMS = "a,b,c,d,e,f,g,h,i,j,k,l,m,n,o,p,q,r,s,t,u,v,w,x,y,z,A,B,C,D,E,F,G,H,I,J,K,L,M,N,O,P,Q,R,S,T,U,V,W,X,Y,Z,_,$,aa,ab,ac,ad,ae,af,ag".split(',')

def split_args_commasafe(args_str):
    """Split comma-separated args respecting nested brackets."""
    parts = []
    current = ''
    depth = 0
    for c in args_str:
        if c == ',' and depth == 0:
            parts.append(current)
            current = ''
        else:
            if c in '([{': depth += 1
            elif c in ')]}': depth -= 1
            current += c
    if current:
        parts.append(current)
    return parts

def build_param_map(args_str):
    raw = split_args_commasafe(args_str)
    pmap = {}
    for i, p in enumerate(PARAMS):
        if i < len(raw):
            v = raw[i].strip()
            if v.startswith('"') and v.endswith('"'):
                v = v[1:-1].replace('\\\\u002F', '/').replace('\\\\u003D', '=').replace('\\\\u0026', '&').replace('\\\\u3000', '\\u3000')
            pmap[p] = v
    return pmap

def resolve(val, pmap):
    v = val.strip()
    if not v:
        return v
    if v.isdigit():
        return int(v)
    if len(v) == 1 and v in pmap:
        # Recurse to resolve chains like Z -> ab -> "1144901"
        nv = pmap[v]
        if nv.startswith('"') and nv.endswith('"'):
            return pmap[v]  # return the quoted string as resolved reference
        return resolve(nv, pmap)
    return pmap.get(v, v)

# ── Title parsing ──
def extract_author(title):
    m = re.search(r'\[([^\]]+)\]', title)
    return m.group(1) if m else None

def lookup_author(title):
    for key, author in KNOWN_AUTHORS.items():
        if key in title:
            return author
    return None

CN_NUMERALS = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}

def extract_volume(title):
    clean = re.sub(r'\[.*?\]', '', title).strip()
    patterns = [
        (r'第(\d+)卷', '第{0}卷'),
        (r'至第(\d+)话', '至第{0}话'),
        (r'第(\d+)话', '第{0}话'),
        (r'[（(](上|下)[）)]', '{0}'),
        (r'[（(](全|完|已完结)[）)]', '已完结'),
    ]
    for pat, fmt in patterns:
        m = re.search(pat, clean)
        if m:
            return fmt.format(*m.groups())
    m = re.search(r'\s0?(\d+)[\s\u3000]', clean)
    if m:
        n = int(m.group(1))
        if 1 <= n < 50:
            return f'第{n}卷'
    m = re.search(r'(\d+)$', clean)
    if m:
        n = int(m.group(1))
        if n < 50:
            return f'第{n}卷'
    m = re.search(r'[^\d](\d+)[)$）]', clean)
    if m:
        n = int(m.group(1))
        if 1 <= n < 50:
            return f'第{n}卷'
    # Chinese numeral at end of title: e.g. "花街之巅 三" = volume 3
    cn_match = re.search(r'\s([一二三四五六七八九十])$', clean)
    if cn_match:
        n = CN_NUMERALS.get(cn_match.group(1))
        if n:
            return f'第{n}卷（{cn_match.group(1)}）'
    return '—'

def clean_title(title):
    t = re.sub(r'\[.*?\]\s*', '', title).strip()
    t = re.sub(r'\u3000+', ' ', t)
    return t

# ── Main ──
def main(html_path, days=3, near_days=5, week_days=7):
    with open(html_path, 'r') as f:
        html = f.read()

    # Extract NUXT state
    idx = html.find('window.__NUXT__=')
    if idx < 0:
        print("ERROR: NUXT state not found in HTML")
        sys.exit(1)
    end_idx = html.find('</script>', idx)
    nuxt = html[idx:end_idx]

    params_match = re.search(r'window\.__NUXT__=\(function\(([^)]+)\)\{return ', nuxt)
    if not params_match:
        print("ERROR: Could not parse NUXT function")
        sys.exit(1)

    last_close = nuxt.rfind('}(')
    args_end = nuxt.find('));', last_close)
    data_obj = nuxt[params_match.end():last_close]
    args_str = nuxt[last_close+2:args_end]

    pmap = build_param_map(args_str)

    # Find LN section
    ln_idx = data_obj.find('more_params:"3,106,1"')
    if ln_idx < 0:
        print("ERROR: LN section not found")
        sys.exit(1)

    section_start = ln_idx
    depth = 0
    while section_start > 0:
        section_start -= 1
        c = data_obj[section_start]
        if c == '}': depth += 1
        elif c == '{':
            if depth == 0: break
            depth -= 1

    next_section = data_obj.find('},{gid:', ln_idx)
    if next_section < 0:
        next_section = data_obj.find('},{', ln_idx)
    section_end = next_section + 1 if next_section > 0 else len(data_obj)
    ln_section = data_obj[section_start:section_end]

    # Parse ranks
    all_entries = {}
    ranks_start = ln_section.find('ranks:[')
    if ranks_start >= 0:
        ranks_part = ln_section[ranks_start+7:]
        rank_positions = [m.start() for m in re.finditer(r'\{rank:', ranks_part)]
        rank_positions.append(len(ranks_part))
        for i in range(len(rank_positions)-1):
            chunk = ranks_part[rank_positions[i]:rank_positions[i+1]].rstrip(', \t\n\r')
            aid_m = re.search(r'aid:(\w+)', chunk)
            title_m = re.search(r'title:"((?:[^"\\]|\\.)*)"', chunk)
            time_m = re.search(r'time:"([^"]*)"', chunk)
            if aid_m and title_m:
                aid_raw = aid_m.group(1)
                aid = int(aid_raw) if aid_raw.isdigit() else int(resolve(aid_raw, pmap))
                title = title_m.group(1).replace('\\u002F', '/').replace('\\u003D', '=').replace('\\u0026', '&').replace('\\u3000', '\u3000')
                time_str = time_m.group(1) if time_m else None
                dt = None
                if time_str:
                    try:
                        dt = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=CST)
                    except: pass
                all_entries[aid] = {'aid': aid, 'title': title, 'time': dt, 'time_str': time_str, 'source': 'ranks'}

    # Parse items
    items_start = ln_section.find('items:[')
    if items_start >= 0:
        items_part = ln_section[items_start+7:]
        item_positions = [m.start() for m in re.finditer(r'\{id:', items_part)]
        item_positions.append(len(items_part))
        for i in range(len(item_positions)-1):
            chunk = items_part[item_positions[i]:item_positions[i+1]].rstrip(', \t\n\r')
            aid_m = re.search(r'action_params:(\w+)', chunk)
            title_m = re.search(r'title:"((?:[^"\\]|\\.)*)"', chunk)
            pic_m = re.search(r'pic_url:"((?:[^"\\]|\\.)*)"', chunk)
            if aid_m and title_m:
                aid_raw = aid_m.group(1)
                aid = int(aid_raw) if aid_raw.isdigit() else int(resolve(aid_raw, pmap))
                title = title_m.group(1).replace('\\u002F', '/').replace('\\u003D', '=').replace('\\u0026', '&').replace('\\u3000', '\u3000')
                pic = pic_m.group(1).replace('\\u002F', '/').replace('\\u003D', '=').replace('\\u0026', '&') if pic_m else ''
                dt = None; ts_str = None
                t_match = re.search(r'[?&]t=(\d+)', pic)
                if t_match:
                    ts = int(t_match.group(1))
                    if 1_000_000_000 < ts < 2_000_000_000:
                        dt = datetime.fromtimestamp(ts, tz=CST)
                        ts_str = dt.strftime('%Y-%m-%d %H:%M')
                if aid not in all_entries:
                    all_entries[aid] = {'aid': aid, 'title': title, 'time': dt, 'time_str': ts_str, 'source': 'items'}
                elif all_entries[aid]['time'] is None and dt is not None:
                    all_entries[aid]['time'] = dt
                    all_entries[aid]['time_str'] = ts_str

    # Categorize
    cutoff = NOW - timedelta(days=days)
    near_cutoff = NOW - timedelta(days=near_days)
    week_cutoff = NOW - timedelta(days=week_days)
    recent, near_miss, week_older = [], [], []

    for aid in sorted(all_entries, reverse=True):
        e = all_entries[aid]
        author = extract_author(e['title'])
        if not author: author = lookup_author(e['title'])
        volume = extract_volume(e['title'])
        display_title = clean_title(e['title'])

        entry = {'aid': aid, 'title': display_title, 'author': author or '未知',
                 'volume': volume, 'time': e['time'], 'time_str': e['time_str']}

        if e['time']:
            if e['time'] >= cutoff: recent.append(entry)
            elif e['time'] >= near_cutoff: near_miss.append(entry)
            elif e['time'] >= week_cutoff: week_older.append(entry)

    # Report
    print(f"## 📚 轻之国度 · 日轻/韩轻翻译区 更新报告\n")
    print(f"**抓取时间**：{NOW.strftime('%Y-%m-%d %H:%M')} CST | **数据源**：首页 SSR | **窗口**：{cutoff.strftime('%m/%d')}–{NOW.strftime('%m/%d')} | **目录**：[category/3/106](https://www.lightnovel.cn/category/3/106)\n")

    if recent:
        print(f"### 🆕 最近{days}天（{len(recent)}本）\n")
        for i, e in enumerate(recent, 1):
            ts = e['time_str'][5:10] if e['time_str'] and len(e['time_str']) >= 10 else '—'
            url = f"https://www.lightnovel.cn/cn/article/{e['aid']}"
            print(f"{i}. **{e['title']}**")
            print(f"   └ 作者：{e['author']} | 卷数：{e['volume']} | 更新：{ts} | [阅读]({url})")
            print()
    else:
        print("### 🆕 最近{days}天：**暂无更新**\n".format(days=days))

    if near_miss:
        print(f"### ⚠️ {days}~{near_days}天前（{len(near_miss)}本）\n")
        for i, e in enumerate(near_miss, 1):
            ts = e['time_str'][5:10] if e['time_str'] and len(e['time_str']) >= 10 else '—'
            url = f"https://www.lightnovel.cn/cn/article/{e['aid']}"
            print(f"{i}. {e['title']} → 作者：{e['author']} | {e['volume']} | {ts} | [aid={e['aid']}]({url})")
        print()

    print("---")
    print("💡 仅收录日轻/韩轻翻译，已过滤国产网文。'未知' 作者为 items 列表新条目，作者信息待 rank 收录后补全。")


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('html_file', help='Path to downloaded lightnovel.fun HTML')
    p.add_argument('--days', type=int, default=3, help='Recent window in days')
    p.add_argument('--near-days', type=int, default=5, help='Near-miss window in days')
    p.add_argument('--week-days', type=int, default=7, help='Week window in days')
    args = p.parse_args()
    main(args.html_file, args.days, args.near_days, args.week_days)
