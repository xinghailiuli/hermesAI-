---
name: qq-attachment-processor
description: >-
  Process files and images the user sends via messaging platforms (primarily QQ).
  Covers image OCR via Tesseract for screenshots, and Office document (.docx/.xlsx)
  extraction, answer-filling, and generation. Handles QQ-specific delivery constraints,
  cache file location, and PYTHONPATH quirks for non-venv packages.
triggers:
  - user sends an image or screenshot
  - read this image or what does this say
  - user sends a .docx .doc .xlsx .pptx file via QQ
  - user says /doc or /document followed by a file
  - fill in answers / 把答案填进去 / 标序号
  - user sends a file attachment that needs text extraction
---

# QQ (and General) Attachment Processing

Process incoming file attachments — both images (for OCR) and Office documents
(for text extraction, answer-filling, and generation). While designed for QQ,
the OCR techniques apply to any platform.

## 1. Locating the Cached File

### Images

Images sent via chat are cached at:
```
~/.hermes/image_cache/img_<hash>.<ext>
```

List recent image cache entries:
```bash
ls -la ~/.hermes/image_cache/
```

### Document files (.docx, .doc, .xlsx, .pptx)

QQ document attachments are stored at:
```
~/.hermes/cache/documents/doc_<hash>_qqdownload<random>
```

These are binary files (not renamed with .docx extension). Use `file` to confirm type:
```bash
file ~/.hermes/cache/documents/doc_*
# → "Microsoft Word 2007+"
```

List recent cache entries:
```bash
ls -la ~/.hermes/cache/documents/
```

**⚠️ QQ filenames are lost**: The cache filename is a hash — the original filename
from QQ is not preserved. You must infer the document type from content analysis.

---

## 2. Image OCR via Tesseract

When the agent cannot natively view images (no vision tools), use tesseract OCR
to extract text from screenshots.

### Prerequisites

```bash
# System packages (includes chi_sim + chi_tra + eng)
sudo apt-get install -y tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-chi-tra

# Python bindings (install into hermes venv)
/opt/pipx/venvs/hermes-agent/bin/python -m pip install pytesseract Pillow
```

### Basic Pipeline

```python
import pytesseract
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
        break
```

Contrast boost (2.0x) is the single most impactful step for Chinese text.

### Preprocessing Pipeline (fallback)

For stubborn images, try additional modes:

```python
from PIL import Image, ImageFilter, ImageEnhance

img = Image.open(path)
gray = img.convert('L')

# 1. Sharpen
sharp = gray.filter(ImageFilter.SHARPEN)
text = pytesseract.image_to_string(sharp, lang='chi_sim+eng')

# 2. Binary threshold
bw = gray.point(lambda x: 0 if x < 128 else 255)
text = pytesseract.image_to_string(bw, lang='chi_sim+eng')

# 3. All PSM modes
for psm in [3, 4, 6, 11, 12]:
    text = pytesseract.image_to_string(high_contrast, lang='chi_sim+eng', config=f'--psm {psm}')
    print(f"PSM {psm}: {text[:200]}")
```

### Pitfalls — Image OCR

- Run OCR in **execute_code**, not terminal. The terminal tool has no PIL or tesseract in its PATH context.
- Always try multiple preprocessing modes. Dark-mode dashboards often need contrast enhancement (2.0x) + PSM 6.
- Chinese+English mixed text: use `lang='chi_sim+eng'` (simplified) or `chi_tra+eng` (traditional).
- Large images (2400px+ width): tesseract handles them fine but preprocessing takes 2-5s per variant.
- Purely visual content (photos, drawings without text): OCR returns garbage — recognize this and tell the user.

---

## 3. Office Document Processing (.docx / .xlsx)

### Install python-docx

python-docx installs to `~/.local` (not the hermes pipx venv):

```bash
pip3 install python-docx --break-system-packages
# → installs to ~/.local/lib/python3.12/site-packages
```

Or install directly into the hermes venv:
```bash
/opt/pipx/venvs/hermes-agent/bin/python -m pip install python-docx
```

**IMPORTANT**: The hermes agent's python does NOT include `~/.local` in sys.path.
Always prefix calls with:
```bash
PYTHONPATH=/home/admin/.local/lib/python3.12/site-packages python3 script.py
```

Or use `execute_code` after installing into the venv (preferred for interactive loops).

### Extracting Text from .docx

```python
import docx
doc = docx.Document(path)
for para in doc.paragraphs:
    if para.text.strip():
        print(para.text)
```

### Generating Output .docx

When creating new docx files (e.g. filling in answers), save to a dedicated output directory:

```python
os.makedirs(os.path.expanduser("~/城乡规划考试资料"), exist_ok=True)
```

Use `docx.Document()` + `add_paragraph()` with bold section titles and normal body text.
Set font to SimSun (宋体), size 11pt for body, 14pt for section headers, 16pt for document title centered.

### Common Task: Fill Answers + Numbering

When the user asks "把答案填进去标序号":

1. Parse the original docx to get the question text + answer key (usually at the end under "参考答案")
2. Build numbered question items: `1. Question text (A Answer)`
3. For multiple-choice: write answer inline in parentheses
4. For true/false: mark `✓` (U+2713) or `✗` (U+2717)
5. Maintain the original section structure (单选题/多选题/判断题/论述题)
6. Include the answer reference text for 论述题

### Sending Generated Files Back — QQ Limitation

**QQ Bot limitation**: The `send_message` tool does NOT route MEDIA attachments to QQ.
When you try, the message sends but MEDIA files are silently dropped:

```
"MEDIA attachments were omitted for qqbot"
"native send_message media delivery is currently only supported for telegram, discord, matrix, weixin, signal, yuanbao and feishu"
```

**Do NOT attempt** to send generated .docx files back via QQ send_message.

### Recommended approach: Offer 3 options

Present the user with a clear choice:

1. **Upload to a temporary file sharing site** and give them a download link
2. **Tell the user the absolute path** on the server for SCP/SFTP download
3. **Paste the full content as formatted text** directly in the chat (for shorter documents)

Use `clarify()` with these 3 options, or suggest option 2 with a concrete path for technical users.

### Pitfalls — Office Documents

- **Two files in a row**: User may send theory paper first, then skill paper. Check both cached files — they're distinguished by content, not filename. Always parse both to identify which is which.
- **python-docx NOT in venv**: It installs to `~/.local`. Always use PYTHONPATH or install it into the hermes venv explicitly.
- **Chinese quotation marks in f-strings**: Avoid nesting Chinese curly quotes (""/「」) inside Python f-strings or triple-quoted strings. Use variables (e.g., `LB = "\u201c"`) and f-string interpolation instead.
- **Large documents**: docx.paragraphs iteration is fine for exam papers (50-100 paragraphs). For larger documents, consider reading only specific sections.
- **Avoid inline code for complex docx generation**: When generating .docx with Chinese text and Unicode symbols (✓✗①②), write the Python code to a `.py` file first with `write_file()`, then execute with `PYTHONPATH=... python3 script.py`. This avoids shell escaping issues.
- **Multiple cached documents**: When user sends multiple files in sequence, check BOTH cache entries. They're distinguished by content, not filename. Always parse all to identify which document is which.

---

## Reference files

- `references/tesseract-ocr.md` — Tesseract troubleshooting guide: preprocessing parameters, OCR accuracy tips, common failure modes, and version-specific notes
