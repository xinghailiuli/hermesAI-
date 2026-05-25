# Galgame Catalog Reference Data

> Last updated: 2026-05-22
> Asset strategy: Local `images/` folder (zip-sharing via QQ)

## Cover Image Mapping (cm)

| Game ID | Title | images/ Path | Source VNDB CDN URL |
|---------|-------|-------------|---------------------|
| 1 | ATRI -My Dear Moments- | images/atri.jpg | https://t.vndb.org/cv/12/76012.jpg |
| 2 | 樱花萌放 | images/sakuramoyu.jpg | https://t.vndb.org/cv/71/79671.jpg |
| 3 | 终之Stella | images/tsui_stella.jpg | https://t.vndb.org/cv/15/75915.jpg |
| 6 | 素晴日 HD | images/subahibi.jpg | https://t.vndb.org/cv/17/90017.jpg |
| 7 | 白昼梦的青写真 | images/hakuchumu.jpg | https://t.vndb.org/cv/17/85317.jpg |
| 12 | 天使☆骚骚 RE-BOOT! | images/tenshi_soudou.jpg | https://t.vndb.org/cv/66/88666.jpg |
| 13 | 星空铁道与白的旅行 | images/soratetsu.jpg | https://t.vndb.org/cv/15/92115.jpg |
| 14 | PARQUET | images/parquet.jpg | https://t.vndb.org/cv/91/79891.jpg |
| 15 | 初音岛5 | images/dc5.jpg | https://t.vndb.org/cv/12/86612.jpg |
| 16 | 常轨脱离Creative凸 | images/hamidashi_totsu.jpg | https://t.vndb.org/cv/91/81091.jpg |
| 19 | 夏日口袋 | images/summer_pockets.jpg | https://t.vndb.org/cv/30/85430.jpg |
| 24 | 苍之彼方的四重奏 | images/aokana.jpg | https://t.vndb.org/cv/55/79855.jpg |
| 30 | 千恋万花 | images/senren_banka.jpg | https://t.vndb.org/cv/46/80746.jpg |
| 31 | 樱云＊ | images/sakura_no_kumo.jpg | https://t.vndb.org/cv/78/90878.jpg |
| 33 | 素晴日 完整版 | images/subahibi.jpg | (same as G6) |

## Background & CG Images

| Asset | images/ Path | Source |
|-------|-------------|--------|
| Body background | images/summer_pockets_bg.jpg | galgame_assets/bg/summer_pockets_bg.jpg |
| Summer Pockets CG1 | images/sp_cg1.jpg | galgame_assets/cg_screenshots/sp_cg1.jpg |
| Summer Pockets CG2 | images/sp_cg2.jpg | galgame_assets/cg_screenshots/sp_cg2.jpg |

## VNDB API Queries (for verification)

### Covers found by ID
- ATRI (v27448) → https://t.vndb.org/cv/12/76012.jpg
- 樱花萌放 (v22313) → https://t.vndb.org/cv/71/79671.jpg
- 素晴日 (v3144) → https://t.vndb.org/cv/17/90017.jpg
- 天使☆骚骚 (v40520) → https://t.vndb.org/cv/66/88666.jpg
- 初音岛5 (v36687) → https://t.vndb.org/cv/12/86612.jpg
- 常轨脱离 (v33205) → https://t.vndb.org/cv/91/81091.jpg
- 樱云 (v26664) → https://t.vndb.org/cv/78/90878.jpg
- PARQUET (v31807) → https://t.vndb.org/cv/91/79891.jpg

### Covers found by search
- 终之Stella → search "Tsui no Stella" → v29443 → https://t.vndb.org/cv/15/75915.jpg
- 白昼梦的青写真 → search "Hakuchuumu no Aojashin" → v26987 → https://t.vndb.org/cv/17/85317.jpg
- 星空铁道 → search "Hoshizora Tetsudou to Shiro no Tabi" → v28297 → https://t.vndb.org/cv/15/92115.jpg
- Summer Pockets → search "Summer Pockets" → v20424 → cover https://t.vndb.org/cv/30/85430.jpg
- 苍之彼方 → search "苍之彼方" → cover https://t.vndb.org/cv/55/79855.jpg
- 千恋万花 → search "千恋万花" → cover https://t.vndb.org/cv/46/80746.jpg

### Summer Pockets Screenshots (SP CGs)
VNDB ID: v20424
- Screenshot [0]: https://t.vndb.org/sf/74/111674.jpg (used as body background)
- Screenshot [1]: https://t.vndb.org/sf/76/111676.jpg (→ images/sp_cg1.jpg)
- Screenshot [2]: https://t.vndb.org/sf/77/111677.jpg (→ images/sp_cg2.jpg)

## Music (Web Audio BGM — no files needed)

8 tracks using real-time synthesized chords:

| # | Name | Chord Progression | Mood |
|---|------|-------------------|------|
| 1 | 🌅 夏日之风 | C → Am → F → G | Bright, uplifting |
| 2 | 🌙 夜空 | Am → F → C → G | Melancholic |
| 3 | 🌸 樱花 | F → G → Em → Am | Romantic |
| 4 | 💭 回忆 | C → G → Am → F | Nostalgic |
| 5 | 🌟 希望 | Dm → G → C → F | Hopeful |
| 6 | 🍂 夏末 | Am → G → F → E7 | Bittersweet |
| 7 | 🌌 梦境 | Fmaj7 → G6 → Em7 → Am7 | Dreamy, jazzy |
| 8 | 🚀 启程 | C → F → G → C | Resolute |

BPM: 76, BEAT: 60/76 ≈ 0.789s, each chord = 4 beats ≈ 3.16s, each track ≈ 12.6s loop.

## Current Restore Point
- Timestamp: 2026.5.21.1.29
- Label: 原点版本
- Location: `Desktop/galgame_versions/2026.5.21.1.29_原点版本/`
- Features: 7 themes, 15 games, Summer Pockets bg, 8 Web Audio tracks, fireworks, message board, shikimori card, dual-device responsive
