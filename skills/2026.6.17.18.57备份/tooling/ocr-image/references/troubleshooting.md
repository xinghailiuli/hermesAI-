# OCR 故障排除

## 环境
- tesseract-ocr: `sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-chi-tra`
- Python: `/opt/pipx/venvs/hermes-agent/bin/python -m pip install pytesseract Pillow`（需要 sudo）

## 预处理选项
| 场景 | 推荐 |
|------|------|
| 截图文字 | 灰度 + Contrast×2，PSM 6 |
| 表格/数据 | 灰度 + 二值化，PSM 3 |
| 混合内容 | 不预处理，PSM 11 或 3 |

## 常见问题
- **识别乱码**：确认 `lang='chi_sim+eng'`，检查是不是繁体（换 `chi_tra`）
- **输出为空**：试试不预处理直接 OCR，或换 PSM 模式
- **低对比度**：`ImageEnhance.Contrast(gray).enhance(3.0)`
