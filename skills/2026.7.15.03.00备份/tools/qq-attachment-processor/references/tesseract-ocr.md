# Tesseract OCR — Troubleshooting & Reference

## Prerequisite Install

```bash
sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-chi-tra
/opt/pipx/venvs/hermes-agent/bin/python -m pip install pytesseract Pillow
```

## Multi-PSM Strategy

PSM (Page Segmentation Mode) values and when to use them:

| PSM | Mode | Best For |
|-----|------|----------|
| 3 | Fully automatic (default) | General text with natural layout |
| 4 | Single column of text | Dashboards, log output |
| 6 | Single uniform block of text | Code screenshots, terminal output |
| 11 | Sparse text (no specific order) | UI elements, scattered labels |
| 12 | Sparse text with OSD | Mixed orientation content |

## Known Failure Modes

1. **Dark mode screenshots** → Contrast enhancement (2.0x) + PSM 6 is the most effective combination
2. **Small text / low DPI** → Try upscaling (2x) before OCR: `img.resize((w*2, h*2), Image.LANCZOS)`
3. **Overlapping text** → Binary threshold (`point(lambda x: 0 if x < 128 else 255)`) can separate layers
4. **Photos of documents with perspective** → tesseract has no deskew; need PIL affine transform first
5. **Purely visual images (no text)** → OCR returns garbage; recognize this and report to user

## Chinese + English Mixed Text

Always use `lang='chi_sim+eng'` for simplified Chinese, `chi_tra+eng` for traditional.
The `+` joins multiple language models. Order doesn't matter for accuracy but `chi_sim+eng` is conventional.

## Performance Notes

- 2400px+ width images: tesseract processes them fine but PIL preprocessing takes 2-5 seconds
- Each PSM variant takes ~1-3 seconds
- Binary threshold is fastest; contrast enhancement is slower but more reliable
