#!/usr/bin/env python3
"""
Galgame Curated Fetch Pipeline for VNDB Kana API (v2).

Three-phase pipeline that produces a ready-to-format JSON array:
  Phase 1: Query VNDB for Chinese-supported VNs (3-month window, 3 pages)
  Phase 2: Classify into categories and select <= 8 candidates
  Phase 3: Batch-fetch full details and save to /tmp/vndb_curated.json

Usage:
  python3 curate_pipeline.py
  python3 format_report.py < /tmp/vndb_curated.json

Output: /tmp/vndb_curated.json (overwritten each run)
"""

import json, urllib.request, os, sys
from datetime import datetime

FIELD_SET = (
    "id, title, alttitle, released, image.url, image.sexual, image.violence, "
    "description, titles.lang, titles.title, titles.official, "
    "developers.name, platforms, languages, rating"
)

def vndb_request(filters, fields=FIELD_SET, results=40, page=1):
    body = json.dumps({
        "filters": filters,
        "fields": fields,
        "sort": "released",
        "reverse": True,
        "results": results,
        "page": page
    }).encode()
    req = urllib.request.Request(
        "https://api.vndb.org/kana/vn", data=body,
        headers={"Content-Type": "application/json"}, method="POST"
    )
    resp = urllib.request.urlopen(req, timeout=30)
    return json.loads(resp.read())


def get_cn_title(vn):
    for t in vn.get('titles', []):
        if t['lang'] in ('zh-Hans', 'zh-Hant', 'zh'):
            return t['title']
    return None


def compute_date_windows():
    today = datetime.now()
    today_str = today.strftime('%Y-%m-%d')
    # Phase 1: 3-month window
    p1 = today.replace(day=1)
    if p1.month >= 4:
        p1 = p1.replace(month=p1.month - 3)
    else:
        p1 = p1.replace(year=p1.year - 1, month=p1.month + 9)
    # Phase 2: 2-month window
    p2 = today.replace(day=1)
    if p2.month >= 3:
        p2 = p2.replace(month=p2.month - 2)
    else:
        p2 = p2.replace(year=p2.year - 1, month=p2.month + 10)
    return p1.strftime('%Y-%m-%d'), p2.strftime('%Y-%m-%d'), today_str


def run_pipeline():
    p1_lower, p2_lower, today_str = compute_date_windows()
    print(f"Phase 1 window: {p1_lower} to {today_str}", file=sys.stderr)

    phase1_filters = ["and",
        ["or", ["lang", "=", "zh-Hans"], ["lang", "=", "zh-Hant"]],
        ["released", ">=", p1_lower],
        ["released", "!=", "TBA"],
        ["released", "<=", today_str]
    ]

    all_phase1 = []
    for page in [1, 2, 3]:
        r = vndb_request(phase1_filters, page=page)
        all_phase1.extend(r['results'])
        if not r.get('more'):
            break

    cn_with_desc, cn_no_desc, multi_lang = [], [], []
    for vn in all_phase1:
        langs = vn.get('languages', [])
        if langs and all(l in ('zh-Hans', 'zh-Hant', 'zh') for l in langs):
            (cn_with_desc if vn.get('description') else cn_no_desc).append(vn)
        else:
            multi_lang.append(vn)

    cn_with_desc.sort(key=lambda v: (v.get('rating') or 0, v.get('released', '')), reverse=True)
    cn_no_desc.sort(key=lambda v: (v.get('rating') or 0, v.get('released', '')), reverse=True)

    candidates = []
    candidates.extend(cn_with_desc[:5])
    recent_no_desc = [v for v in cn_no_desc if v.get('released', '') >= p1_lower]
    candidates.extend(recent_no_desc[:2])
    multi_recent = [v for v in multi_lang
                    if v.get('released', '') >= p2_lower and (v.get('rating') or 0) >= 60]
    multi_recent.sort(key=lambda v: (v.get('rating') or 0, v.get('released', '')), reverse=True)
    candidates.extend(multi_recent[:3])

    seen = set()
    unique = []
    for vn in candidates:
        if vn['id'] not in seen:
            seen.add(vn['id'])
            unique.append(vn)
    final = unique[:8]

    id_filters = ["or"] + [["id", "=", vn['id']] for vn in final]
    detail_resp = vndb_request(id_filters, results=len(final))
    detail_map = {vn['id']: vn for vn in detail_resp['results']}
    curated = [detail_map.get(vn['id'], vn) for vn in final]

    os.makedirs('/tmp', exist_ok=True)
    with open('/tmp/vndb_curated.json', 'w', encoding='utf-8') as f:
        json.dump(curated, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(curated)} entries to /tmp/vndb_curated.json", file=sys.stderr)
    for vn in curated:
        cn = get_cn_title(vn)
        langs = vn.get('languages', [])
        is_cn = bool(langs and all(l in ('zh-Hans', 'zh-Hant', 'zh') for l in langs))
        print(f"  {'CN' if is_cn else 'ML'} v{vn['id']}: {cn or vn['title']} | "
              f"{vn.get('released')} | rating={vn.get('rating', 'N/A')}", file=sys.stderr)


if __name__ == '__main__':
    run_pipeline()
