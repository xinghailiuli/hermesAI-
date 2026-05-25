---
name: web-frontend-prototypes
description: Build self-contained single-file HTML prototypes with interactive effects. Use when user asks for a quick web UI, catalog, dashboard, or showcase site — no frameworks, no build step, just open the file.
triggers:
  - user wants a website/gallery/catalog/dashboard
  - user asks for CSS animations or interactive effects
  - user wants something "好看" / "有特效" / "二次元风格"
---

# Web Frontend Prototypes

Build polished single-file HTML pages with embedded CSS and JS. No npm, no frameworks, no server needed — the user opens the file in a browser.

## Template Structure

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>...</title>
  <style>
    /* All CSS inline */
  </style>
</head>
<body>
  <!-- All HTML here -->
  <script>
    // All JS inline
  </script>
</body>
</html>
```

## Interactive Effects Library

See `references/interactive-effects.md` for ready-to-copy CSS+JS blocks (starfield, sakura petals, click ripples, sparkles, cursor glow, card hover effects).

## Dark Anime Theme (Default: Black)

Default palette should use pure black tones, not dark purple:\n\n```\nBackground:  #080614\nSurface:     rgba(8,4,16,0.72) + backdrop-filter: blur(10px)\nText:        #d8d0e8 (soft lavender white)\nText muted:  rgba(190,180,210,0.55)\nPink accent: #ff6b9d\nPurple:      #c471f5\nBlue accent: #7ec8e3\nBorders:     rgba(255,107,157,0.06)\nGradient:    linear-gradient(135deg, #ff6b9d, #c471f5, #7ec8e3)\nBackground overlay: linear-gradient(180deg, rgba(0,0,0,0.75), rgba(0,0,0,0.6), rgba(0,0,0,0.85))\n```

## Cover Image Sourcing (Galgame / Game Databases)

When the user wants real cover art for game entries in a catalog:

1. **Use VNDB API** — NEVER guess VNDB cover image IDs. Query properly:
   ```python
   # POST to https://api.vndb.org/kana/vn
   data = {"filters": ["search", "=", "Exact Title"], "fields": "id,title,image.url,image.id", "results": 3}
   ```
2. **Cover URL format:** `https://t.vndb.org/cv/{last_two_digits_of_cover_id}/{full_cover_id}.jpg`
3. **Batch with execute_code** for 10+ games — faster than individual curl calls.
4. **Download to local assets:** `curl -sL -o covers/name.jpg -H "User-Agent: Mozilla/5.0" -H "Referer: https://vndb.org/" "$url"`
5. **Some games aren't on VNDB** (mobile gacha like Heaven Burns Red, action-RPG hybrids like Fate/Samurai Remnant). Generate PIL placeholders with game name text.
6. **Verify after download:** `stat -c%s file.jpg` — reject files under 2KB as error pages.

See `references/vndb-api.md` for full query patterns.

## Music Player

Two approaches, ordered by reliability for local `file://` HTML:

### A. Web Audio API (RECOMMENDED for local files)
YouTube/NetEase embeds fail on `file://` protocol. Use the browser's built-in Web Audio API instead — no files, no network, works 100% locally:

```js
let audioCtx = null, playing = false, oscNodes = [];
function getAC() {
  if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  if (audioCtx.state === 'suspended') audioCtx.resume(); // CRITICAL for autoplay policy
  return audioCtx;
}
function stopAll() { oscNodes.forEach(o => { try { o.stop() } catch(e) {} }); oscNodes = []; }
function playTone(freq, start, dur, vol) {
  const ctx = getAC(), o = ctx.createOscillator(), g = ctx.createGain();
  o.type = 'triangle'; // richer than sine
  o.frequency.value = freq;
  g.gain.setValueAtTime(0, start);
  g.gain.linearRampToValueAtTime(vol * 0.25, start + 0.02);
  g.gain.exponentialRampToValueAtTime(0.001, start + dur);
  o.connect(g); g.connect(ctx.destination); oscNodes.push(o);
  o.start(start); o.stop(start + dur + 0.05);
}
function playMelody(notes, bpm) {
  stopAll(); const ctx = getAC(), bl = 60 / bpm;
  notes.forEach((freq, i) => {
    const t = ctx.currentTime + i * bl * 0.5;
    playTone(freq, t, bl * 0.45, 0.5);
    playTone(freq / 2, t, bl * 0.45, 0.15); // octave harmony
  });
}
```

**Critical:** Always call `audioCtx.resume()` in `getAC()` — browsers suspend AudioContext until user gesture. Without it, no sound plays even after click.

**Note frequencies:** Use C5 range (523Hz+) for audibility on laptop speakers. Triangle waveform sounds warmer than sine. Track oscillators in an array so `stopAll()` can clean up.

### B. YouTube Embed (only for hosted/server-served pages)
Only works when HTML is served via http://, not file://. Use hidden iframe with `?autoplay=1`. Not recommended for local desktop prototypes.

## Background Image with Dark Overlay

For galgame-themed sites where a game screenshot serves as the page background:
```css
body {
  background-image: url('bg/summer_pockets_bg.jpg');
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  position: relative;
}
body::before {
  content: ''; position: fixed; inset: 0; z-index: 0;
  background: linear-gradient(180deg,
    rgba(10,8,24,0.65) 0%,
    rgba(10,8,24,0.85) 50%,
    rgba(10,8,24,0.92) 100%);
}
body::after {
  content: ''; position: fixed; inset: 0; z-index: 0;
  background: radial-gradient(ellipse at 30% 20%, rgba(255,107,157,0.08) 0%, transparent 50%),
              radial-gradient(ellipse at 70% 60%, rgba(126,200,227,0.08) 0%, transparent 50%);
}
/* All content must sit above the overlays */
.container { position: relative; z-index: 1; }
```
This preserves the atmospheric background while ensuring text readability. Download screenshots from VNDB (`image.screenshots[].url` field) for authentic game backgrounds.

## Search with Autocomplete

For catalogs with 15+ items:
- Build a suggestion index from all searchable fields (titles, developers, character names, CVs, tags).
- Use a dropdown positioned below the search input with keyboard navigation (↑↓ Enter Esc).
- Deduplicate by `type+text` key: `[...new Map(suggestions.map(s => [s.type+s.text, s])).values()]`.
- Close dropdown on outside click: `document.addEventListener('click', e => { if (!e.target.closest('.search-wrap')) ... })`.

## Music: Real MP3 Files

When the user supplies their own music file, use native `<audio>` — simplest and most reliable:

```js
let audio = new Audio('galgame_assets/music/song.mp3'), playing = false;
audio.loop = true; audio.volume = 0.5;
function togglePlay() {
  if (!playing) { audio.play().catch(e => {}); playing = true; }
  else { audio.pause(); playing = false; }
  // Update UI button state...
}
```

No external APIs, no Web Audio oscillators — just play the file. Prefer this over Web Audio API when a real audio file is available.

### Multi-Track Player with Loop & Shuffle

When the user adds multiple songs to a `music/` folder, build a full playlist player:

```js
const musicFiles = ['song1.mp3', 'song2.mp3', ...]; // scan or hardcode
let audio = new Audio(), playing = false, curIdx = -1;
let loopMode = 2; // 0=off, 1=single-loop, 2=play-all
let shuffleOn = false, playlist = [...musicFiles];
audio.volume = 0.5;

function loadIdx(i) {
  if (i < 0 || i >= playlist.length) return;
  curIdx = i; audio.src = getPath(playlist[i]);
  // Update dot indicators...
}
audio.addEventListener('ended', () => {
  if (loopMode === 1) { audio.currentTime = 0; audio.play(); }
  else if (loopMode === 2) nextTrack();
  else { playing = false; updateUI(); }
});
function nextTrack() {
  if (shuffleOn) curIdx = Math.floor(Math.random() * playlist.length);
  else curIdx = (curIdx + 1) % playlist.length;
  loadIdx(curIdx); if (playing) audio.play().catch(e => {});
}
function toggleLoop() { loopMode = (loopMode + 1) % 3; updateUI(); }
function toggleShuffle() { shuffleOn = !shuffleOn; updateUI(); }
```

**UI buttons:** ▶ play/pause, ⏮ prev, ⏭ next, 🔁 loop toggle (all/single/off), 🔀 shuffle toggle, 🎮 restart-from-first.

## Theme Switcher (Dark/Pink/Light)

Single-file CSS custom properties + JS toggle. Define 3 theme objects, switch via `document.documentElement.style.setProperty()`:

```js
const themes = {
  dark:  {'--card-bg': 'rgba(18,10,35,0.65)', '--text': '#e8e0f8', '--pink': '#ff6b9d', ...},
  pink:  {'--card-bg': 'rgba(35,10,25,0.65)', '--text': '#f8e0ec', '--pink': '#ff85b3', ...},
  light: {'--card-bg': 'rgba(255,248,254,0.7)', '--text': '#4a3050', '--pink': '#e87090', ...},
};
let curTheme = 0;
function switchTheme() {
  curTheme = (curTheme + 1) % 3;
  Object.entries(themes[['dark','pink','light'][curTheme]])
    .forEach(([k, v]) => document.documentElement.style.setProperty(k, v));
}
```

Use `var(--card-bg)` throughout CSS so all styles respond to theme changes instantly — no page reload needed. Button: `<button class="theme-btn" onclick="switchTheme()">🎨</button>`. Place in header.

## Mini Character Click Effects

See `references/interactive-effects.md` — added Murasame (千恋万花) and Shiroha (Summer Pockets) CSS-art click effects. Each creates a small CSS-styled chibi character that pops up and floats away on click.

## Placeholder Removal

When a game entry has only a generated placeholder cover (VNDB couldn't source it), **remove it from the catalog**. Placeholders make the site look incomplete. Better to have 15 games with real covers than 18 with 3 fakes. User explicitly asked: "把所有没有封面或者封面不对的全部删除，只留封面正确的."

## Pitfalls

- **NEVER do full file rewrites when iterating.** Users hate it when working features vanish. Always: (1) identify specific issues, (2) use targeted `patch` tool edits, (3) verify nothing was lost. This is the #1 user-frustration trigger.
- **Ship check: always verify against disk before declaring done.** After any file-reference change (covers, music, images), run `ls -la` or `stat` to confirm actual filenames, sizes, and paths match what the code references. "It should work" = not verified.
- JS property name mismatch — THREE forms of this bug are common:
  - `g.id` vs `g.i`: When using shorthand constructors like `function G(i){return {i}}`, the key is `i` not `id`. Using `g.id` silently returns undefined → blank images everywhere.
  - **HTML `onclick` vs JS function names**: `<button onclick="togglePlay()">` but JS defines `function tp()`. Mismatch → button does nothing with no error. Grep both sides before declaring done.
  - **Music playlist filenames vs disk**: JS array has `'Mix-.mp3'` but actual file is `'宇多田ヒカル - Beautiful World -PLANiTb Acoustica Mix-.mp3'`. Always `ls -la music/` and copy exact filenames.
- Web Audio: browsers suspend AudioContext until user gesture. MUST call `audioCtx.resume()` inside `getAC()`. Without it, no sound on first click.
- VNDB cover images: NEVER fabricate CV IDs. VN ID =/= cover image ID. Always query the API.
- **Local file:// blocks external links**: `target="_blank"` and `window.open()` are blocked by browsers from local HTML files. Use `window.location.href = url` in onclick handler for reliable link opening. Pure `<a>` tags with `href` also work but `target="_blank"` will be silently ignored.
- **Autoplay blocked globally**: All modern browsers block `audio.play()` without user gesture. Pattern: call `autoPlay()` on init → if `.catch()` fires, show hint "👆 点击页面任意位置开始播放" → use `document.addEventListener('click', startOnce, {once:true})`.
- **Mobile touch clicks**: Browsers sometimes fire `click` but not on `<div>` pseudo-links. Add `ontouchend` handler in addition to `onclick` for mobile reliability. Use `<div>` not `<a>` when you need JS-controlled navigation from `file://` pages.
- **MUSIC ON ANDROID: audio.load() before audio.play()**: On mobile Chrome, if `audio.play()` is blocked once by autoplay policy, that Audio element is **permanently locked** — subsequent `play()` calls silently fail even after user gesture. FIX: call `audio.load()` immediately before `audio.play()` in the user-triggered handler. This resets the element's blocked state. Pattern:
  ```js
  function startMusic() {
    if (musicReady || playing) return;
    musicReady = true; loadIdx(0); playing = true;
    audio.load();  // ← CRITICAL: reset blocked audio element
    audio.play().then(() => updateUI()).catch(() => { playing = false; musicReady = false; });
  }
  ```
  Also: override `togglePlay` to check `musicReady` flag and call `audio.load()` on first real play. Show pulsing play button when blocked to guide the user.

## Mobile / Android Adaptation

For single-file HTML viewed on Android/phone:
- Viewport meta: `maximum-scale=1.0,user-scalable=no,viewport-fit=cover`
- PWA meta: `apple-mobile-web-app-capable`, `mobile-web-app-capable`
- Touch: `-webkit-tap-highlight-color:transparent;touch-action:manipulation`
- Breakpoints: 768px (tablet, 2-col cards), 480px (phone, 1-col cards)
- Disable hover on mobile, use `:active` with `scale(0.96)` for tap feedback
- Min button size: 28px for touch targets
- Reduce petal size/quantity for mobile performance

## Music Player — Merge Mode Buttons

Instead of separate loop/shuffle/restart buttons, merge into one cycling button like NetEase Cloud:
- 🔂 Single repeat → 🔀 Shuffle → 🔁 List loop
- Add mute toggle (🔊/🔇 changes color when muted)
- Add volume slider + clickable progress bar with `timeupdate` listener

```js
let playMode = 2; // 0=single, 1=shuffle, 2=list-loop
function toggleMode() { playMode = (playMode + 1) % 3; updateUI(); }
function toggleMute() { audio.muted = !audio.muted; btn.textContent = audio.muted ? '🔇' : '🔊'; }

// Progress bar - click to seek, auto-updates during playback
audio.addEventListener('timeupdate', () => {
  const bar = document.getElementById('mProgress');
  if (bar && audio.duration) bar.value = (audio.currentTime / audio.duration) * 100;
});
function seekTo(e) {
  const bar = e.target, rect = bar.getBoundingClientRect();
  const pct = (e.clientX - rect.left) / rect.width;
  if (audio.duration) audio.currentTime = pct * audio.duration;
}
```

HTML bar layout: `[song title] [dots] [⏮] [▶] [⏭] [mode btn] [mute btn] [volume slider] [progress bar]`

## Resource Site Links — Copy URL Button

For friend-link sections, add a per-card copy-URL button that doesn't interfere with the main click-to-navigate action:

```js
function renderRSites() {
  rSites.forEach(s => {
    const a = document.createElement('div');
    a.className = 'rs-card';
    a.onclick = function() { window.location.href = s.url; };
    a.innerHTML = `<div class="rsi">${s.icon}</div><h4>${s.name}</h4>
      <div class="rsu">👉 ${s.url.replace('https://','')}</div><p>${s.desc}</p>
      <button class="copy-btn" onclick="event.stopPropagation();copyURL('${s.url}')">📋 复制链接</button>`;
    c.appendChild(a);
  });
}
function copyURL(url) {
  navigator.clipboard.writeText(url).then(() => {
    // Show brief success feedback
  }).catch(() => { prompt('复制链接:', url); }); // fallback for HTTP/file://
}
```

Use `event.stopPropagation()` on the copy button so it doesn't trigger the card's navigation onclick.
