---
name: single-file-html-dev
description: Build and maintain single-file HTML applications with PC+mobile sync. Covers audio, links, touch handling, cover images, and iterative patching discipline.
---

# Single-File HTML App Development

Trigger: user asks to build, edit, or maintain a single-file HTML application (static site, catalog, gallery, player, dashboard).

## CRITICAL RULES

### Never Full Rewrite
**NEVER delete working features and rewrite from scratch.** The user has explicitly rejected this pattern multiple times. Always:
1. Identify specific issues via targeted reads/searches
2. Use `patch` tool for surgical fixes
3. Verify nothing was lost after each patch
4. If you must rewrite a section, copy the old code first and compare

### PC + Mobile Sync
Every change MUST work on both desktop and mobile simultaneously. One bug = two fixes.

### Permanent Restore Point
When the user designates a version as the canonical restore target, respect it. When user says "还原" or "回退" or "返回上一版", restore to the designated version — don't guess.

## Mobile-Specific Patterns

### Audio on Mobile
```javascript
// ALWAYS use encodeURIComponent for file paths with Chinese/japanese chars
function getPath(f){return'folder/'+encodeURIComponent(f)}

// Mobile browsers permanently lock blocked Audio elements.
// Create FRESH Audio on first user tap:
function newAudio(){
  if(audio){audio.pause();audio.src='';audio=null}
  audio=new Audio();audio.volume=0.5;
}

// Use BOTH click and touchend events
document.addEventListener('touchend', startMusic);
document.addEventListener('click', startMusic);
```

### Links from file://
`target="_blank"` and `window.open()` are BLOCKED from local HTML files.
Use `window.location.href = url` instead (navigates same tab).

### Touch vs Hover
- No `:hover` effects on mobile — use `:active` only
- Buttons ≥28px for touch targets
- `-webkit-tap-highlight-color:transparent`
- `touch-action:manipulation` on body

## JS Bugs to Watch

### Property name mismatch
When using shorthand object constructors, verify property names:
```javascript
// BAD: function returns {i:...} but code uses g.id
function G(i,...){return{i:i,...}}
cm[g.id] // undefined

// FIX: either use g.i or change constructor to {id:i}
cm[g.i] // works
```

### HTML onclick vs JS function names
```html
<button onclick="togglePlay()"> <!-- but JS defines function tp() -->
```
Mismatch → button does nothing. Grep both sides.

### Music filenames vs disk
JS array has `'Mix-.mp3'` but actual file is `'宇多田ヒカル - Beautiful World...mp3'`. Always `ls -la music/` and copy exact filenames before coding.

## Cover Image Sources — Priority Order (China-Accessible)

### STRATEGY 1 (PREFERRED): Local `images/` folder with relative paths
**Use this FIRST for any Chinese-accessible deployment.** The user has repeatedly chosen this over CDN alternatives.

1. Create `images/` folder next to the HTML
2. Copy covers, background, CG screenshots from `galgame_assets/` into it
3. Reference as `images/atri.jpg` in `cm` mapping
4. Zip `galgame_catalog.html` + `images/` together for distribution

```javascript
const cm = {
  1: 'images/atri.jpg',
  2: 'images/sakuramoyu.jpg',
  // ... all covers use images/ prefix
};
body::before{background:url('images/summer_pockets_bg.jpg')...}
<img src=\"images/sp_cg1.jpg\">
```

**Why this is preferred:**
- `t.vndb.org` (VNDB CDN) takes 10-25s per image from Chinese networks — partially fails
- catbox.moe, 0x0.st, gofile.io, s-ul.eu — all blocked/timeout from China
- wsrv.nl image proxy — also slow from China
- Base64 embedding bloats HTML to 3-4MB
- Local images load instantly, no internet dependency

### STRATEGY 2 (Fallback): VNDB CDN URLs
Only use when local images/ folder is impossible. Query carefully:
- POST to `api.vndb.org/kana/vn`, search by title, get `image.url`
- VNDB image ID ≠ VN ID — must query API
- Downloaded covers < 2000 bytes = failed download
- Check with `stat -c%s` after each curl
- For screenshots: use `screenshots.url` field
- Search by Japanese/English title if Chinese title returns nothing

### STRATEGY 3 (Last resort): Base64 inline embedding
Downloads all covers, converts to data:image/jpeg;base64,... URLs in the `cm` mapping.
- Expects ~3.1MB for 15 covers
- Covers load instantly with no network
- Makes HTML file very large — only use when zip distribution is impossible

## Music — Two Approaches

### A. Local MP3 via HTML5 Audio
- Use HTML5 `<Audio>` with `encodeURIComponent` paths for local files
- On mobile: `audio.load()` before `audio.play()` resets blocked audio element

### B. Web Audio API BGM Synthesizer (no files needed)
**Use when the HTML must be self-sufficient** (shared via QQ/WeChat, no `galgame_assets/` folder).

Architecture:
1. Define chord progressions as arrays of chord names (e.g. `['C','Am','F','G']`)
2. Map chord names to frequency arrays (e.g. `C:[261.63,329.63,392.00]`)
3. At BPM~76, each chord lasts 4 beats, so a 4-chord loop = ~12.6s
4. Use `OscillatorNode` (triangle for root, sine for others) + `GainNode` envelope:
   - `gain.linearRampToValueAtTime(vol, start+0.12)` for fade-in
   - `gain.linearRampToValueAtTime(0, end-0.25)` for fade-out
5. Add LFO chorus on root note: `lfo.connect(lfoGain).connect(osc.frequency)`
6. Add random arpeggio on double-octave with probability ~60%
7. Expose a `createBGM()` factory returning an object with `.play()/.pause()/volume/currentTime/duration` + `addEventListener('timeupdate'|'ended')` — so existing UI code works unchanged
8. Call `audioCtx.resume()` on first play (browser autoplay policy)

Key implementation skeleton:
```javascript
const BPM=76,BEAT=60/BPM;
const CHORDS={C:[261.63,329.63,392.00], Dm:[293.66,349.23,440.00], ...};
const TRACKS=[{name:'🌅 夏日之风',prog:['C','Am','F','G']}, ...];
function createBGM(){
  let ctx=null,gain=null,_vol=0.5,_playing=false,_off=0,_start=0,_dur=12,_idx=-1;
  let _sch=[],_timer=null,_endCbs=[],_timeCbs=[];
  function getC(){if(!ctx)ctx=new AudioContext();return ctx}
  function stopAll(){_sch.forEach(n=>{try{n.osc.stop()}catch(e){}});_sch=[]}
  function sched(idx,off){
    const c=getC();stopAll();
    const prog=TRACKS[idx].prog,cd=BEAT*4;
    _dur=prog.length*cd;const now=c.currentTime;
    prog.forEach((ch,ci)=>{
      const fr=CHORDS[ch]||CHORDS.C,cs=now+ci*cd-off;
      fr.forEach((f,fi)=>{
        const o=c.createOscillator(),g2=c.createGain();
        o.type=fi===0?'triangle':'sine';o.frequency.value=f;
        // ... gain envelope + optional LFO
        g2.connect(gain);o.start(st);o.stop(et+0.05);_sch.push({osc:o,gain:g2});
      });
    });
    _timer=setInterval(()=>{_playing&&_timeCbs.forEach(f=>f())},150);
  }
  // ... return interface object
}
```

## Image Loading Optimization

### Primary CSS (User-Approved)
The user provided this cleaner CSS for skeleton loading + image fade-in:

```css
/* Skeleton shimmer */
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
.skeleton-card {
  background: linear-gradient(90deg, #e8e8e8 25%, #f5f5f5 50%, #e8e8e8 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite linear;
  border-radius: 8px;
}

/* Image fade-in */
.game-img { opacity: 0; transition: opacity 0.6s ease; }
.game-img.loaded { opacity: 1; }
```

### Theme-Matched Alternative (for dark UIs)
When the page has a dark/colored theme, use transparent shimmer overlays instead of light gray:

```css
.gci{background:linear-gradient(135deg,#1a1030,#2a1845)} /* placeholder color */
.gci::after{content:'';position:absolute;inset:0;
  background:linear-gradient(110deg,transparent 30%,rgba(255,255,255,0.03) 50%,transparent 70%);
  background-size:200% 100%;animation:shimmer 1.8s infinite;pointer-events:none;z-index:1}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
.gci img{opacity:0;transition:opacity 0.6s ease;position:relative;z-index:2}
.gci img.loaded{opacity:1}
.gci.loaded::after{opacity:0;transition:opacity 0.5s}
```

### JS Handler (on each `<img>`)
```html
<img ... loading="lazy"
  onload="this.classList.add('loaded');this.parentElement.classList.add('loaded')"
  onerror="this.style.display='none';this.parentElement.style.background='...'">
```

### Key Points
- Shimmer hides itself + image fades in simultaneously via `.loaded` class cascade
- `loading="lazy"` reduces concurrent requests for offscreen images
- `onerror` still fires — shows gradient placeholder if source is unreachable

## Local Image Folder Strategy

### For Website Deployment (this user's primary)
The user deploys to a **web server** and shares URLs (not ZIP files). When user says "发网址" or "网站", do NOT suggest ZIP packaging:
1. Create `images/` folder next to `galgame_catalog.html`
2. Copy ALL needed assets there (covers, background, CG screenshots)
3. Upload both the HTML and `images/` folder to the web server
4. Relative paths `images/atri.jpg` resolve from the web root
5. Visitors open the URL and see everything instantly

### For QQ/WeChat File Sharing (alternative — only if user explicitly asks to send files)
1. Zip `galgame_catalog.html` + `images/` into one archive
2. Send zip to QQ group / WeChat
3. Recipients unzip and everything works locally, no internet needed

### Why local images (not CDN)
- `t.vndb.org` (VNDB CDN) is **very slow from China** — 10-25 seconds per image, partial failure
- catbox.moe, 0x0.st, gofile.io, s-ul.eu, upload.ee — all blocked/timeout from Chinese networks
- wsrv.nl (image proxy) — also slow from China
- Base64 embedding makes HTML 3-4MB — local images are cleaner
```
Desktop/
├── galgame_catalog.html
├── images/
│   ├── atri.jpg          ← covers/
│   ├── sakuramoyu.jpg
│   ├── summer_pockets.jpg ← covers_new/
│   ├── summer_pockets_bg.jpg  ← bg/
│   ├── sp_cg1.jpg        ← cg_screenshots/
│   └── sp_cg2.jpg
└── galgame_assets/       ← original assets, keep for reference
```

### cm Mapping Pattern
```javascript
const cm = {
  1: 'images/atri.jpg',
  2: 'images/sakuramoyu.jpg',
  // ... all 15 covers use images/ prefix
};
```

For background (CSS) and CG (modal):
```css
body::before {
  background: url('images/summer_pockets_bg.jpg') center/cover no-repeat fixed;
}
```
```javascript
if(g.i===19){
  h+=`<img src=\"images/sp_cg1.jpg\" ...>`;
  h+=`<img src=\"images/sp_cg2.jpg\" ...>`;
}
```

### If CDN Must Be Used (fallback)
VNDB API query pattern for screenshots:
```javascript
POST https://api.vndb.org/kana/vn
{"filters":["search","=","Summer Pockets"],"fields":"id,title,screenshots.url,screenshots.dims","results":3}
```

Note: If `image.url` is empty, search by Japanese title instead of Chinese. VNDB image ID ≠ VN ID.

## Workflow: Pivot Don't Brute-Force
When the primary approach fails (e.g. file hosting unreachable, API rate-limited, search returns nothing):
- **Don't** retry the same approach with different endpoints/credentials 3+ times
- **Do** assess what alternative approaches exist for the same goal:
  - Can't upload music files? → Synthesize with Web Audio API
  - Can't find game on VNDB? → Search by Japanese/English title, or verify VNDB ID manually
  - Can't reach external CDN? → Use VNDB's own CDN (covers + screenshots)
- User explicitly flagged "不要一根筋" (don't be stubborn about one method)

## Fireworks Click Effect
Replace character click effects with explosive colorful particle bursts using Web Animations API (`element.animate()`). 10 colors, 12-20 particles per click, radial explosion, auto-removed on finish.

## Theme System: 7 Themes
Expand from 3 to 7 presets via CSS custom properties: dark, pink, gold, green, ocean, midnight, light. Each theme object defines --card-bg, --text, --muted, --pink, --purple, etc. Cycle with `(curTheme + 1) % 7`.

## Message Board with localStorage
Persistent guestbook: nickname + text inputs, submit via button or Enter. Stores to `localStorage`, capped at 50 entries. Renders with timestamps. Survives theme changes and page reloads.

## Custom Animated Progress Bar (replacing `<input type="range">`)
Native range inputs look out of place in styled UIs. Replace with custom div-based progress bars:

```html
<div class="music-progress" id="mProgressBar" onclick="seekTo(event)" title="拖动进度">
  <div class="music-progress-fill" id="mProgressFill" style="width:0%"></div>
  <div class="chibi chibi-left">🦊</div>
  <div class="chibi chibi-right">🐱</div>
</div>
```

```css
.music-progress{position:relative;width:120px;height:8px;background:rgba(255,255,255,0.06);border-radius:4px;cursor:pointer;overflow:visible}
.music-progress-fill{height:100%;border-radius:4px;background:linear-gradient(90deg,#ff6b9d,#ffd700,#50e890,#4ea8e8,#c471f5,#ff6b9d);background-size:200% 100%;animation:rainbow-bar 2.5s linear infinite;transition:width 0.15s ease}
@keyframes rainbow-bar{0%{background-position:0% 50%}100%{background-position:200% 50%}}
```

Key points:
- Use `background-size: 200%` + `background-position` animation for flowing rainbow effect
- JS: `fill.style.width = (currentTime/duration)*100 + '%'` on `timeupdate`
- `seekTo(e)`: compute `(e.clientX - rect.left) / rect.width`, clamped 0-1, set `audio.currentTime`
- Both `seekTo` and any play/pause toggle must call `e.stopPropagation()` to avoid global click handler conflicts
- Chibi characters: absolute-positioned emoji in circles with `chibi-hop` bounce animation, `pointer-events:none` so they don't intercept clicks

## Pitfalls
- **NEVER do full file rewrites.** Always use `patch`.
- **Verify against disk:** `ls -la` after any file-reference change.
- **JS property name mismatches:** g.i vs g.id, onclick vs function name, playlist filenames vs disk files.
- **Mobile autoplay blocked:** audio element permanently locked after first failed play(). Fix: call `audio.load()` before `audio.play()` in user-triggered handler.
- **file:// blocks external links:** Use `window.location.href` for navigation.
- **window.scrollTo needs prefix:** `scrollTo(...)` fails silently; use `window.scrollTo({top:0,behavior:'smooth'})`.
- **CSS in wrong location breaks form inputs:** A `<style>` block between `</footer>` and `<script>` caused input fields to become unresponsive. Always put CSS in the main `<style>` block in `<head>`, never inline after body elements.
- **Inline onclick unreliable for dynamic elements:** `onclick="postMsg()"` failed on a dynamically-constructed button. Use `addEventListener('click', fn)` in JS instead — it always binds regardless of DOM construction order.
- **Form inputs need explicit inline styles on dark themes:** CSS variable `var(--input-bg)` may not cascade into elements outside main containers. Use explicit `background:rgba(0,0,0,0.6);color:#e0d8f0` on input elements inside footer/board sections.
- **Version folder asset paths break:** When HTML is copied into `galgame_versions/<timestamp>/`, relative paths like `galgame_assets/covers/x.jpg` break because they resolve from the version folder, not Desktop. Fix: create Windows directory junction to `galgame_assets/` inside the version folder.
- **Global click handler hijacks pause button:** If a `document.addEventListener('click')` calls `audio.play()` and sets `playing=true`, clicking the pause button fires both the button's `togglePlay()` (pauses) AND the global handler (re-plays immediately). Fix: (a) `togglePlay(e)` calls `e.stopPropagation()`, (b) global click handler checks `if(e.target.closest('button,.mbtn,.music-bar'))return;`, (c) `seekTo()` also calls `stopPropagation()`.
- **VNDB CDN is unusably slow from China:** `t.vndb.org` takes 10-25s per image from Chinese networks. Some images may partially fail. Do NOT rely on VNDB CDN for Chinese users — use local `images/` folder + zip sharing instead.
- **File hosting is unreliable from China:** catbox.moe, 0x0.st, gofile.io, s-ul.eu, wsrv.nl, upload.ee are all blocked, timing out, or require registration from Chinese networks. Do not attempt to upload assets to these services for Chinese users — they will not load.
- **Pivot don't brute-force (用户说要灵活):** When the primary approach fails 2-3 times (file host unreachable, API search returns nothing, CDN slow), STOP retrying the same pattern and switch to a fundamentally different approach. The user explicitly flagged "不要一根筋" — they want creative pivoting, not stubborn retries. E.g.: can't host MP3s → synthesize with Web Audio API; can't host images → local images/ folder + zip; VNDB search fails → try Japanese/English title.
- **WSL → Windows file encoding:** Writing `.ps1` or `.bat` files from WSL that contain non-ASCII characters (Chinese, emoji) often produces garbled encoding on the Windows side. PowerShell scripts fail with `ParserError` / `MissingArrayIndexExpression`. **Fix:** Use `schtasks.exe` directly instead of PowerShell scripts, or write ASCII-only scripts. For desktop shortcuts, use `.url` INI-format files (ASCII-safe).

## Deployment Context
This user runs a **website** (URL-based deployment), not file sharing. Key implications:
- Don't suggest ZIP packaging — the user sends URLs, not files
- `images/` folder must be uploaded alongside the HTML to the web server
- Relative paths like `images/atri.jpg` resolve correctly when both exist on the same server
- Covers load fast because they're on the same server, not from a remote CDN
- Web Audio BGM works on the website (no local MP3s needed)
- The `galgame_catalog.html` is deployed as a static site — no backend required

## Version Tracking System
When the user designates a version as canonical:
1. Create `Desktop/galgame_versions/年.月.日.时.分_描述/` folder — use CURRENT date-time, NOT incremented vX.X. User explicitly rejected `v1.0_原点` in favor of timestamp format like `2026.5.21.1.29_原点版本`.
2. Copy current `galgame_catalog.html` into it
3. Create a Windows directory junction to `galgame_assets/` inside the version folder so relative asset paths resolve. From WSL: `/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe -Command "New-Item -ItemType Junction -Path '<version_folder>\galgame_assets' -Target '<desktop>\galgame_assets'"`. Without this, covers/backgrounds/music will all 404 because the HTML uses relative `galgame_assets/...` paths that resolve relative to the version folder location.
4. Write `更新日志.txt` with version number, date, feature list, music list, cover sources, bug fixes
5. Update memory with new restore point using `memory action=replace`

On every future update, repeat steps 1-5 with current timestamp.

## Reference Data
See `references/galgame-data.md` for verified VNDB cover IDs, exact music filenames, CG screenshot URLs, and the current 15-game list.
See `references/windows-junction.md` for the exact PowerShell junction command and troubleshooting.
See `references/china-accessible-sites.md` for a list of reference/research websites that work from this user's Chinese network environment — use these when web searches time out. Also includes Chinese AI API provider endpoints (通义千问/豆包/智谱/硅基流动) for building API relay stations.