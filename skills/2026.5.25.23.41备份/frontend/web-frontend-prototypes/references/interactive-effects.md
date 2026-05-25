# Interactive Effects: Copy-Paste CSS + JS

Ready-to-copy blocks for common anime-themed web effects. Each block is self-contained — copy CSS to `<style>`, JS to `<script>`.

## 1. Starfield / Twinkling Background

Creates 80 randomized stars that pulse with different timing.

**CSS:**
```css
.stars-bg { position: fixed; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:0; }
.star {
  position: absolute; background: #fff; border-radius: 50%;
  animation: twinkle var(--dur) ease-in-out infinite;
  animation-delay: var(--delay);
}
@keyframes twinkle {
  0%,100% { opacity: 0.3; transform: scale(1); }
  50%   { opacity: 1; transform: scale(1.5); }
}
```

**HTML:** `<div class="stars-bg" id="starsBg"></div>`

**JS:**
```js
const bg = document.getElementById('starsBg');
for(let i=0; i<80; i++){
  const s = document.createElement('div');
  s.className = 'star';
  s.style.cssText = `left:${Math.random()*100}%;top:${Math.random()*100}%;width:${1+Math.random()*2.5}px;height:${s.style.width};--dur:${2+Math.random()*4}s;--delay:${Math.random()*4}s;`;
  bg.appendChild(s);
}
```

---

## 2. Sakura Petal Fall

Continuous falling petals from top of screen.

**CSS:**
```css
.petal-container { position: fixed; top:0; left:0; width:100%; height:100%; pointer-events:none; z-index:9999; }
.petal {
  position: absolute; top: -10%; font-size: 1.2rem;
  animation: petalFall linear forwards; pointer-events: none; opacity: 0.7;
}
@keyframes petalFall {
  0%   { transform: translateY(0) rotate(0deg) translateX(0); opacity:0.9; }
  50%  { transform: translateY(50vh) rotate(180deg) translateX(60px); opacity:0.7; }
  100% { transform: translateY(110vh) rotate(360deg) translateX(-30px); opacity:0; }
}
```

**HTML:** `<div class="petal-container" id="petalContainer"></div>`

**JS:**
```js
const petalEmojis = ['🌸','💮','🌺','✿','❀','🌷','💐'];
let petalsActive = true;

function spawnPetal(){
  if(!petalsActive) return;
  const p = document.createElement('div');
  p.className = 'petal';
  p.textContent = petalEmojis[Math.floor(Math.random()*petalEmojis.length)];
  p.style.cssText = `left:${Math.random()*98}%;font-size:${0.8+Math.random()*1.5}rem;animation-duration:${8+Math.random()*10}s;animation-delay:${Math.random()*3}s;`;
  document.getElementById('petalContainer').appendChild(p);
  setTimeout(()=>p.remove(), 16000);
}
setInterval(spawnPetal, 1800);
for(let i=0;i<6;i++) setTimeout(spawnPetal, i*400);

// Toggle button
function togglePetals(){
  petalsActive = !petalsActive;
  btn.textContent = petalsActive ? '🌸' : '🍂';
  if(!petalsActive) document.getElementById('petalContainer').innerHTML = '';
}
```

---

## 3. Click Ripple + Sparkle Burst

Colorful ripples and flying emoji sparkles on every click.

**CSS:**
```css
.ripple {
  position: fixed; border-radius: 50%; pointer-events: none; z-index: 10000;
  animation: rippleOut 0.8s ease-out forwards;
}
@keyframes rippleOut {
  0%   { width:0; height:0; opacity:1; border-width:4px; }
  100% { width:120px; height:120px; opacity:0; border-width:1px; margin-left:-60px; margin-top:-60px; }
}
.sparkle {
  position: fixed; pointer-events: none; z-index: 10001;
  font-size: 1rem;
  animation: sparkleFade 0.7s ease-out forwards;
}
@keyframes sparkleFade {
  0%   { opacity:1; transform: scale(1) translateY(0); }
  100% { opacity:0; transform: scale(0.3) translateY(-30px); }
}
```

**JS:**
```js
const rippleColors = ['#ff6b9d','#c471f5','#7ec8e3','#ffd54f'];
const sparkleEmojis = ['✨','💫','⭐','🌟','💖','♪'];

document.addEventListener('click', e=>{
  // Ripple
  const r = document.createElement('div');
  r.className = 'ripple';
  r.style.cssText = `left:${e.clientX}px;top:${e.clientY}px;border:2px solid ${rippleColors[Math.floor(Math.random()*4)]};`;
  document.body.appendChild(r);
  setTimeout(()=>r.remove(), 800);

  // Sparkles
  for(let i=0; i<6; i++){
    const s = document.createElement('div');
    s.className = 'sparkle';
    s.textContent = sparkleEmojis[i] || '✨';
    s.style.cssText = `left:${e.clientX+(Math.random()-0.5)*60}px;top:${e.clientY+(Math.random()-0.5)*60}px;animation-duration:${0.5+Math.random()*0.8}s;`;
    document.body.appendChild(s);
    setTimeout(()=>s.remove(), 800);
  }
});
```

---

## 4. Cursor Glow

Soft colored radial glow following the mouse.

**CSS:**
```css
.cursor-glow {
  position: fixed; pointer-events: none; z-index: 9998;
  width: 200px; height: 200px; border-radius: 50%;
  background: radial-gradient(circle, rgba(255,107,157,0.12) 0%, transparent 70%);
  transform: translate(-50%,-50%); transition: opacity 0.3s;
}
```

**HTML:** `<div class="cursor-glow" id="cursorGlow"></div>`

**JS:**
```js
const glow = document.getElementById('cursorGlow');
document.addEventListener('mousemove', e=>{
  glow.style.left = e.clientX+'px';
  glow.style.top = e.clientY+'px';
});
document.addEventListener('mouseleave', ()=> glow.style.opacity='0');
document.addEventListener('mouseenter', ()=> glow.style.opacity='1');
```

---

## 5. Card Hover Glow (Gradient Border)

Glowing border on card hover using pseudo-element.

**CSS:**
```css
.game-card {
  position: relative; border-radius: 16px; overflow: hidden;
  transition: all 0.4s cubic-bezier(0.4,0,0.2,1);
}
.game-card::before {
  content: ''; position: absolute; inset: -2px; border-radius: 16px;
  background: linear-gradient(135deg, transparent, rgba(255,107,157,0.3), rgba(126,200,227,0.3), transparent);
  opacity: 0; transition: opacity 0.4s; z-index: -1; filter: blur(4px);
}
.game-card:hover::before { opacity: 1; }
.game-card:hover {
  transform: translateY(-8px) scale(1.02);
  box-shadow: 0 16px 40px rgba(196,113,245,0.25);
}
```

---

## 6. Button Ripple (Material-style)

Expanding circle on button press.

**CSS:**
```css
.btn {
  position: relative; overflow: hidden;
}
.btn::after {
  content: ''; position: absolute; top:50%; left:50%;
  width:0; height:0; border-radius: 50%;
  background: rgba(255,255,255,0.2);
  transform: translate(-50%,-50%);
  transition: width 0.6s, height 0.6s;
}
.btn:active::after { width:300px; height:300px; }
```

---

## 8. Mini Character Click Effect (Chibi Pop)

When clicked, a tiny anime character pops up and floats away. Customize the character by changing the CSS shapes and face expression pool.

**CSS:**
```css
.mini-char {
  position: fixed; pointer-events: none; z-index: 10002;
  animation: charPop 1.2s ease-out forwards;
}
.mini-char .char-body {
  width:48px; height:56px; position:relative;
}
/* Body (white dress) */
.mini-char .char-body::before {
  content:''; position:absolute;
  width:32px; height:40px; background:#fff; border-radius:16px 16px 8px 8px;
  left:8px; top:8px;
  box-shadow:0 2px 8px rgba(100,180,220,0.4);
}
/* Hair (light blue) */
.mini-char .char-body::after {
  content:''; position:absolute;
  width:28px; height:20px;
  background:linear-gradient(180deg,#b8dff0,#8ec8e8);
  border-radius:14px 14px 0 0;
  left:10px; top:2px;
}
.mini-char .char-face {
  position:absolute; top:16px; left:50%; transform:translateX(-50%);
  font-size:18px; z-index:1; line-height:1;
}
@keyframes charPop {
  0%   { transform:translateY(0) scale(0) rotate(-20deg); opacity:1; }
  15%  { transform:translateY(-30px) scale(1.2) rotate(5deg); opacity:1; }
  30%  { transform:translateY(-40px) scale(1) rotate(0deg); opacity:1; }
  70%  { transform:translateY(-50px) scale(0.9) rotate(0deg); opacity:0.8; }
  100% { transform:translateY(-80px) scale(0.3) rotate(15deg); opacity:0; }
}
```

**JS:**
```js
document.addEventListener('click', e => {
  const ch = document.createElement('div');
  ch.className = 'mini-char';
  ch.style.left = (e.clientX - 24) + 'px';
  ch.style.top = (e.clientY - 28) + 'px';
  const faces = ['(◕‿◕)','(｡･ω･｡)','(◍•ᴗ•◍)','(＾▽＾)','(✿◠‿◠)'];
  ch.innerHTML = `<div class="char-body"><div class="char-face">${faces[Math.floor(Math.random()*faces.length)]}</div></div>`;
  document.body.appendChild(ch);
  setTimeout(() => ch.remove(), 1300);
});
```

Customize: change hair color gradient in `.char-body::after`, body color in `::before`, and `faces` array for different characters.

### 8a. Emoji-Based Mini Character (Simpler Variant)

For faster implementation, skip CSS art and use an emoji + text bubble:

**CSS:**
```css
.mini-mura { position:fixed; pointer-events:none; z-index:10002; animation:mPop 1.5s ease-out forwards; text-align:center }
.mini-mura .mb { font-size:42px; filter:drop-shadow(0 3px 6px rgba(255,170,80,0.5)) }
.mini-mura .mt { font-size:10px; color:#ffe0c0; text-shadow:0 0 6px rgba(255,170,80,0.5) }
@keyframes mPop {
  0% { transform:translateY(0)scale(0)rotate(-35deg);opacity:1 }
  20% { transform:translateY(-38px)scale(1.3)rotate(5deg) }
  100% { transform:translateY(-90px)scale(0.2)rotate(20deg);opacity:0 }
}
```

**JS:**
```js
document.addEventListener('click', e => {
  if (e.target.closest('button,a,input,select')) return;
  const m = document.createElement('div'); m.className = 'mini-mura';
  m.style.left = (e.clientX-22) + 'px'; m.style.top = (e.clientY-18) + 'px';
  m.innerHTML = '<div class="mb">🦊</div><div class="mt">むらさめ〜</div>';
  document.body.appendChild(m); setTimeout(() => m.remove(), 1600);
});
```

Swap the emoji and text for different characters (e.g., `🐱` + `にゃ～`, `🌸` + `ぽよ〜`).

Sticky floating action buttons in the bottom-right corner.

**CSS:**
```css
.quick-nav { position: fixed; bottom: 24px; right: 24px; z-index: 150; display: flex; flex-direction: column; gap: 10px; }
.quick-nav-btn {
  width: 48px; height: 48px; border-radius: 50%;
  border: 1px solid rgba(196,113,245,0.3);
  background: rgba(30,20,50,0.9); backdrop-filter: blur(6px);
  color: #c8b8e0; font-size: 1.2rem; cursor: pointer;
  transition: all 0.3s;
  display: flex; align-items: center; justify-content: center;
}
.quick-nav-btn:hover {
  background: rgba(196,113,245,0.2); border-color: #c471f5;
  color: #f0e8ff; transform: scale(1.1);
  box-shadow: 0 4px 16px rgba(196,113,245,0.25);
}
```

**HTML:**
```html
<div class="quick-nav">
  <button class="quick-nav-btn" onclick="window.scrollTo({top:0,behavior:'smooth'})" title="Top">⬆</button>
  <button class="quick-nav-btn" onclick="document.getElementById('searchInput').focus()" title="Search">🔍</button>
  <button class="quick-nav-btn" onclick="togglePetals()" title="Toggle petals">🌸</button>
</div>
```
