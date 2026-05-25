---
name: code-quality
description: 写代码与优化技巧，减少bug率。编码规范、常见bug模式、防御性编程、测试策略。
---

# 代码质量 & Bug预防

## 一、命名与属性检查（最常见bug来源）

### 1.1 对象属性名一致性
**这是最高频bug！** 尤其在JS中传参用简写时：
```js
// ❌ 容易出错：简写时属性名和变量名不一致
const game = { id: g.id, title: g.title };
// 后面用了 g.i → undefined，因为属性名是 id 不是 i

// ✅ 始终用完整属性名，别缩写
const game = { id: g.id, title: g.title, cover: g.image?.url };
// 使用时：game.id ✅  game.i ❌
```

### 1.2 变量命名规则
- 驼峰命名：`coverUrl` `musicPlayer` `themeColor`
- 布尔值加前缀：`isPlaying` `hasCover` `isValid`
- 禁止单字母变量（除循环 `i` `j`）
- DOM引用加前缀：`mProgressBar` `btnPlay` `elCard`

## 二、事件处理（高频bug区）

### 2.1 事件冒泡
```js
// ❌ 点击暂停按钮→冒泡到document→又触发播放
btnPause.onclick = function() {
    audio.pause();
}

// ✅ 阻止冒泡
btnPause.onclick = function(e) {
    e.stopPropagation();
    audio.pause();
}

// ✅ 全局监听器排除特定区域
document.addEventListener('click', function(e) {
    if (e.target.closest('.music-bar')) return; // 排除音乐栏
    // 其他逻辑...
});
```

### 2.2 移动端事件
```js
// PC和移动端都要处理
el.addEventListener('click', handler);
el.addEventListener('touchend', function(e) {
    e.preventDefault();
    handler(e);
});
```

### 2.3 防止重复绑定
```js
// ❌ 每次调用都绑新事件→触发N次
function init() {
    btn.onclick = doStuff; // 第2次init会重复绑定
}

// ✅ 先解绑或检查
function init() {
    btn.onclick = null; // 清除旧绑定
    btn.onclick = doStuff;
}
```

## 三、防御性编程

### 3.1 空值检查链
```js
// ❌ 任一环节为null就报错
const cover = data.results[0].image.url;

// ✅ 可选链 + 默认值
const cover = data?.results?.[0]?.image?.url || 'default.jpg';
```

### 3.2 API返回值校验
```python
# ❌ 假设返回值一定存在
resp = requests.get(url)
data = resp.json()
title = data["results"][0]["title"]

# ✅ 每一步都校验
resp = requests.get(url, timeout=15)
if resp.status_code != 200:
    print(f"请求失败: {resp.status_code}")
    return None
data = resp.json()
if not data.get("results"):
    print("无结果")
    return None
title = data["results"][0].get("title", "未知")
```

### 3.3 文件操作校验
```python
# 下载后检查
with open(path, "wb") as f:
    f.write(resp.content)
size = os.path.getsize(path)
if size < 500:  # 小于500B大概率是占位图/错误页
    print(f"⚠️ 文件异常({size}B)，已删除")
    os.remove(path)
    return False
```

### 3.4 边界条件
```js
// 数组访问
const last = arr.length > 0 ? arr[arr.length - 1] : null;

// 数字范围
volume = Math.max(0, Math.min(1, volume));

// 音乐播放前检查
if (audio.readyState >= 2) {
    audio.play();
}
```

## 四、修改代码的铁律

### 4.1 绝不删功能
> ⚠️ **最高优先级原则！** 修复一个bug时，绝不能顺手删掉其他正常工作的功能。

```bash
# ✅ 正确流程：
1. 定位具体问题（哪一行、什么症状）
2. 用 patch 工具做精确替换
3. 改完后验证：被改的功能好了 + 其他功能还在
```

### 4.2 改前确认
改代码前回答三个问题：
1. 这个改动会影响哪些地方？
2. 有没有引用这段代码的其他函数？
3. 改完后用户看到的页面还完整吗？

### 4.3 Patch优于重写
```bash
# ✅ 精确替换一个bug
patch(path, old_string="错误代码行", new_string="修复后代码行")

# ❌ 整个文件重写 → 100%引入新bug + 可能丢掉功能
```

### 4.4 立即停止协议
> ⚠️ 用户说「停止」「别做了」「停下」时，**立刻停手**，不要继续当前操作。
> 不要辩解、不要解释为什么要继续、不要「让我先把这个完成」——立刻停止所有动作，等待用户的下一步指令。

## 五、测试清单

### 5.1 每次修改后快速自查
- [ ] PC端和安卓端都正常
- [ ] 主题切换不报错
- [ ] 音乐播放→暂停→切歌正常
- [ ] 封面图不404
- [ ] 控制台无红色报错
- [ ] 所有按钮点得动

### 5.2 网页端调试
```js
// 在浏览器控制台快速检查
// 检查元素是否存在
document.querySelectorAll('.game-card').length  // 应该=15
// 检查音乐状态
audio.paused  // false=播放中
```

### 5.3 数据库验证SQL
```sql
-- 数据完整性检查
SELECT COUNT(*) FROM games;                    -- 总数
SELECT COUNT(*) FROM games WHERE cover_local IS NULL;  -- 缺封面的
SELECT DISTINCT developer FROM games;          -- 去重检查
```

## 六、常见Bug速查表

| Bug症状 | 常见原因 | 检查点 |
|---------|---------|--------|
| `undefined` | 属性名写错 | `g.i` → 应为 `g.id` |
| 点击无反应 | 事件未绑定/被覆盖 | DOM加载顺序、重复init |
| 点了触发两次 | 事件重复绑定 + 冒泡 | stopPropagation、解绑旧事件 |
| 封面不显示 | 图片下载失败/146B占位 | 检查bytes、URL是否正确 |
| 页面空白 | JS报错阻断渲染 | F12控制台看红字 |
| 音乐不能播放 | 浏览器自动播放限制 | 需用户点击触发 audioCtx.resume() |
| 移动端变形 | CSS未做响应式 | @media (max-width: 768px) |
| API无结果 | 搜索条件太严格/VNDB无收录 | 放宽条件、手动补充 |
| 400模型名错误 | 函数返回dict漏字段 | 检查路由函数return是否包含`model`字段 |

## 七、函数间数据流（高频坑）

### 7.1 返回dict漏字段
**这是今天踩的坑！** 函数A返回dict给函数B用，但A忘了传某个字段，B那边 `dict.get("xxx", default)` 静默退回到default导致错误。
```python
# ❌ resolve_upstream 返回dict漏了 model 字段
def resolve_upstream(name):
    ...
    return {"base_url": url, "api_key": key, "provider": p}

# 调用方
upstream = resolve_upstream(name)
payload["model"] = upstream.get("model", fallback)  # 永远走fallback！

# ✅ 返回时带全字段
def resolve_upstream(name):
    ...
    return {"base_url": url, "api_key": key, "provider": p,
            "model": route.get("model", fallback)}
```
**检查方法**：如果一个 dict 在函数A构造、在函数B消费，去A的 return 语句数一数字段数量对不对。

## 八、编码习惯

1. **写之前想3秒** — 这个变量后面怎么用？
2. **改完立刻测** — 不要攒一堆再测
3. **console.log先留着** — 确认无误再删调试代码
4. **一个patch一个bug** — 不混改
5. **命名要能猜出含义** — `elCard` 好于 `x`
