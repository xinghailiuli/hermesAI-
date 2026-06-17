---
name: image-ocr
description: OCR images to extract text when the user sends screenshots. Uses tesseract + pytesseract with Chinese/English support.
triggers:
  - user sends an image or screenshot
  - read this image or what does this say
  - image contains text charts UI that agent cannot access via vision tools
---

# Image OCR via Tesseract

When the agent cannot natively view images (no vision tools), use tesseract OCR to extract text from screenshots the user sends.

## Prerequisites

```bash
# System packages (includes chi_sim + chi_tra + eng)
sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-chi-tra

# Python bindings (install into hermes venv)
sudo /opt/pipx/venvs/hermes-agent/bin/python -m pip install pytesseract Pillow
```

## Basic Usage

```python
import pytesseract
from PIL import Image

img = Image.open("/home/admin/.hermes/image_cache/img_xxx.jpg")
text = pytesseract.image_to_string(img, lang='chi_sim+eng')
print(text)
```

## Quick Pipeline (preferred)

For most screenshots (dashboards, social media, error messages),
contrast enhancement + multi-PSM is all you need:

```python
from PIL import Image, ImageEnhance

img = Image.open(path)
gray = img.convert('L')
high_contrast = ImageEnhance.Contrast(gray).enhance(2.0)

for psm in [3, 6, 11]:
    text = pytesseract.image_to_string(
        high_contrast, lang='chi_sim+eng', config=f'--psm {psm}'
    )
    if text.strip():
        print(text.strip())
```

Contrast boost (2.0x) is the single most impactful step for Chinese text.
Only fall back to sharpen or binary if this pipeline yields garbage.

## Preprocessing Pipeline (fallback)

For stubborn images, try additional modes:

```python
from PIL import Image, ImageFilter, ImageEnhance

img = Image.open(path)
gray = img.convert('L')

# 1. Sharpen
sharp = gray.filter(ImageFilter.SHARPEN)
print(pytesseract.image_to_string(sharp, lang='chi_sim+eng'))

# 2. High contrast (dark screenshots)
enhancer = ImageEnhance.Contrast(gray)
high_contrast = enhancer.enhance(2.0)
print(pytesseract.image_to_string(high_contrast, lang='chi_sim+eng'))

# 3. Binary threshold
bw = gray.point(lambda x: 0 if x < 128 else 255)
print(pytesseract.image_to_string(bw, lang='chi_sim+eng'))

# 4. Different PSM modes (try 3, 6, 11)
for psm in [3, 6, 11]:
    text = pytesseract.image_to_string(high_contrast, lang='chi_sim+eng', config=f'--psm {psm}')
    print(f"PSM {psm}: {text[:200]}")
```

## Pitfalls

- Run OCR in execute_code, not terminal. The terminal tool has no PIL or tesseract in its PATH context.
- Always try multiple preprocessing modes. Dark-mode dashboards often need contrast enhancement (2.0x) + PSM 6 for best results.
- Chinese+English mixed text: use `lang='chi_sim+eng'` (simplified) or `chi_tra+eng` (traditional).
- Large images (2400px+ width): tesseract handles them fine but preprocessing takes 2-5s per variant.
- Purely visual content (photos, drawings without text): OCR returns garbage -- recognize this and tell the user.
