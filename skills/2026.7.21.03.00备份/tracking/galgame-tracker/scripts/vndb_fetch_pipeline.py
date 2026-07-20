#!/usr/bin/env python3
"""
VNDB fetch pipeline: Phase 1 (Chinese) + Phase 2 (English+Chinese rated).
Queries VNDB API, classifies results, selects up to 8 curated entries,
and saves to /tmp/vndb_curated.json for format_report.py to consume.

Usage (cron mode):
    python3 this_script.py 2>/dev/null
    python3 <skill_dir>/scripts/format_report.py < /tmp/vndb_curated.json

Output:
    - /tmp/vndb_raw_phase1.json — raw Phase 1 results (all pages)
    - /tmp/vndb_raw_phase2.json — raw Phase 2 results
    - /tmp/vndb_curated.json    — up to 8 curated entries for format_report.py
"""
import json
import urllib.request
import sys
from datetime import datetime


def vndb_request(filters, fields=None, results=40, page=1):
    """Make a POST request to the VNDB Kana API."""
    if fields is None:
        fields = (
            "id, title, alttitle, released, image.url, image.sexual, "
            "image.violence, description, titles.lang, titles.title, "
            "titles.official, developers.name, platforms, languages, rating"
        )
    body = json.dumps({
        "filters": filters,
        "fields": fields,
        "sort": "released",
        "reverse": True,
        "results": results,
        "page": page,
    }).encode()
    req = urllib.request.Request(
        "https://api.vndb.org/kana/vn",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def is_chinese_original(langs):
    """True if ALL languages are Chinese variants."""
    return bool(langs) and all(l in ("zh-Hans", "zh-Hant", "zh") for l in langs)


def has_chinese(langs):
    """True if any Chinese variant is present."""
    return any(l in ("zh-Hans", "zh-Hant", "zh") for l in langs)


def get_cn_title(vn):
    """Get Chinese title from titles array (zh-Hans > zh-Hant > zh)."""
    for t in vn.get("titles", []):
        if t["lang"] in ("zh-Hans", "zh-Hant", "zh"):
            return t["title"]
    return None


# ── Date window computation ──────────────────────────────────────────
today = datetime.now()
today_str = today.strftime("%Y-%m-%d")

# Phase 1: 3-month window
m1 = today.month - 3
y1 = today.year
if m1 <= 0:
    m1 += 12
    y1 -= 1
phase1_lower = f"{y1}-{m1:02d}-01"

# Phase 2: 2-month window
m2 = today.month - 2
y2 = today.year
if m2 <= 0:
    m2 += 12
    y2 -= 1
phase2_lower = f"{y2}-{m2:02d}-01"

print(f"Phase 1 window: {phase1_lower} to {today_str}", file=sys.stderr)
print(f"Phase 2 window: {phase2_lower} to {today_str}", file=sys.stderr)

# ── Phase 1: Chinese-first query (page 1 + page 2) ───────────────────
phase1_filters = [
    "and",
    ["or", ["lang", "=", "zh-Hans"], ["lang", "=", "zh-Hant"]],
    ["released", ">=", phase1_lower],
    ["released", "!=", "TBA"],
    ["released", "<=", today_str],
]

print("Fetching Phase 1 page 1...", file=sys.stderr)
p1_p1 = vndb_request(phase1_filters, page=1)
print(f"  Got {len(p1_p1['results'])} results, more={p1_p1.get('more')}", file=sys.stderr)

p1_results = p1_p1["results"]
if p1_p1.get("more"):
    print("Fetching Phase 1 page 2...", file=sys.stderr)
    p1_p2 = vndb_request(phase1_filters, page=2)
    print(f"  Got {len(p1_p2['results'])} results, more={p1_p2.get('more')}", file=sys.stderr)
    p1_results += p1_p2["results"]

print(f"Phase 1 total: {len(p1_results)} results", file=sys.stderr)

# ── Phase 2: Broader query (English + Chinese, rated >= 60) ──────────
phase2_filters = [
    "and",
    ["or", ["lang", "=", "en"], ["lang", "=", "zh-Hans"], ["lang", "=", "zh-Hant"]],
    ["released", ">=", phase2_lower],
    ["released", "!=", "TBA"],
    ["released", "<=", today_str],
    ["rating", ">=", "60"],
]

print("Fetching Phase 2...", file=sys.stderr)
p2 = vndb_request(phase2_filters, page=1)
p2_results = p2["results"]
print(f"Phase 2: {len(p2_results)} results, more={p2.get('more')}", file=sys.stderr)

# ── Classify Phase 1 results ──────────────────────────────────────────
cn_originals = [v for v in p1_results if is_chinese_original(v.get("languages", []))]
cn_supported = [
    v for v in p1_results
    if not is_chinese_original(v.get("languages", []))
    and has_chinese(v.get("languages", []))
]
print(f"Chinese originals: {len(cn_originals)}", file=sys.stderr)
print(f"Chinese-supported multi-lang: {len(cn_supported)}", file=sys.stderr)

for v in cn_originals:
    cn_title = get_cn_title(v) or v.get("title", "?")
    has_desc = bool(v.get("description"))
    print(f"  • {cn_title} | released={v.get('released','?')} | has_desc={has_desc} | rating={v.get('rating',0)}", file=sys.stderr)

# ── Build candidate list ──────────────────────────────────────────────
candidates = []

# Priority 1: Chinese originals with descriptions
candidates.extend(v for v in cn_originals if v.get("description"))

# Priority 2: Chinese originals without descriptions (up to 3)
candidates.extend(v for v in cn_originals if not v.get("description"))[:3]

# Priority 3: Phase 2 Chinese-supported entries
p2_cn = [v for v in p2_results if has_chinese(v.get("languages", []))]
print(f"Phase 2 Chinese-supported: {len(p2_cn)}", file=sys.stderr)

seen_ids = {v["id"] for v in candidates}
for v in p2_cn:
    if v["id"] not in seen_ids:
        candidates.append(v)
        seen_ids.add(v["id"])
        if len(candidates) >= 8:
            break

# Priority 4: Phase 2 English-only (if still need more)
if len(candidates) < 8:
    p2_en = [v for v in p2_results if not has_chinese(v.get("languages", []))]
    for v in p2_en:
        if v["id"] not in seen_ids:
            candidates.append(v)
            seen_ids.add(v["id"])
            if len(candidates) >= 8:
                break

# Limit to 8
final_candidates = candidates[:8]
print(f"\nFinal {len(final_candidates)} candidates selected", file=sys.stderr)

# ── Save outputs ──────────────────────────────────────────────────────
with open("/tmp/vndb_raw_phase1.json", "w") as f:
    json.dump(p1_results, f, ensure_ascii=False, indent=2)

with open("/tmp/vndb_raw_phase2.json", "w") as f:
    json.dump(p2_results, f, ensure_ascii=False, indent=2)

with open("/tmp/vndb_curated.json", "w") as f:
    json.dump(final_candidates, f, ensure_ascii=False, indent=2)

print(f"Saved {len(final_candidates)} curated entries to /tmp/vndb_curated.json", file=sys.stderr)
print("Done.", file=sys.stderr)
