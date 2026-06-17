---
name: ocr-image
description: OCR 识别用户发送的图片文字。用于 vision 工具不可用时的回退方案。
---

# OCR 图片识别

当 Hermes 的 vision 工具不可用时，用 pytesseract + Pillow 做 OCR 回退。

## 触发条件
- 用户发送图片但 Hermes 报 "couldn't quite see it"
- vision_analyze / view_image 不可用或失败

## 步骤

### 1. 尝试 view_image / vision_analyze 优先
调用 `delegate_task(toolsets=["vision"])` 或直接调 vision 工具。只有失败时才走 OCR 回退。

### 2. OCR 回退
`execute_code` 中运行：

```python
import pytesseract
from PIL import Image, ImageEnhance

img = Image.open("<image_path>")
gray = img.convert('L')                          # 灰度
hc = ImageEnhance.Contrast(gray).enhance(2.0)    # 对比度×2

# 多 PSM 模式试一遍
for psm in [3, 6, 11]:
    text = pytesseract.image_to_string(hc, lang='chi_sim+eng', config=f'--psm {psm}')
    if text.strip():
        print(f"--- psm {psm} ---")
        print(text.strip())
```

### 3. 图像获取
图片通常缓存在 `~/.hermes/image_cache/`，系统消息中会给出 `image_url` 路径。

## 局限性
- 对图表、UI 截图效果一般，适合纯文字截图
- 中文准确率约 80-90%，可能需要人工核对
- 不支持手写体、低对比度文字

## 参考
- `references/troubleshooting.md`：故障排除和预处理选项
