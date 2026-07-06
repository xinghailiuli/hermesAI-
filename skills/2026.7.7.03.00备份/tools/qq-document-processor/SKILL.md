---
name: qq-document-processor
description: Handle .docx and other Office document attachments sent via QQ. Covers file location in cache, extraction/parsing, answer-filling, and delivery limitations.
triggers:
  - user sends a .docx .doc .xlsx .pptx file via QQ
  - user says /doc or /document followed by a file
  - fill in answers / 把答案填进去 / 标序号
  - user sends a file attachment that needs text extraction
---

# QQ Document Attachment Processing

When the user sends an Office document (typically .docx exam papers, forms, or tables) via QQ, Hermes receives the file and caches it locally.

## 1. Locating the Cached File

QQ document attachments are stored in:

```
~/.hermes/cache/documents/doc_<hash>_qqdownload<random>
```

These are binary files (not renamed with .docx extension). Use `file` to confirm type:

```bash
file ~/.hermes/cache/documents/doc_*
# → "Microsoft Word 2007+"
```

List recent cache entries with:

```bash
ls -la ~/.hermes/cache/documents/
```

## 2. Parsing .docx Content

### Install python-docx (if not present)

python-docx gets installed to `~/.local` (not the hermes pipx venv):

```bash
pip3 install python-docx --break-system-packages
# → installs to ~/.local/lib/python3.12/site-packages
```

### Extract text (must set PYTHONPATH)

```python
import docx
doc = docx.Document(path)
for para in doc.paragraphs:
    if para.text.strip():
        print(para.text)
```

**IMPORTANT**: The hermes agent's python (`/opt/pipx/venvs/hermes-agent/bin/python3`) does NOT include `~/.local` in sys.path. Always prefix calls with:

```bash
PYTHONPATH=/home/admin/.local/lib/python3.12/site-packages python3 script.py
```

Or use execute_code with the environment set (preferred for interactive loops).

### Generating Output .docx

When creating new docx files (e.g. filling in answers), save to a dedicated output directory:

```python
os.makedirs(os.path.expanduser("~/城乡规划考试资料"), exist_ok=True)
```

Use `docx.Document()` + `add_paragraph()` with bold section titles and normal body text. Set font to SimSun (宋体), size 11pt for body, 14pt for section headers, 16pt for document title centered.

## 3. Sending Back to the User

**QQ platform limitation**: QQ Bot adapter DOES have a `send_document()` method (supports chunked/rich-media file upload), but the `send_message` tool's `_send_to_platform()` at `tools/send_message_tool.py` lines 689-701 does NOT route MEDIA attachments to QQ. When you try, the message sends but MEDIA files are dropped:

```
"MEDIA attachments were omitted for qqbot"
"native send_message media delivery is currently only supported for telegram, discord, matrix, weixin, signal, yuanbao and feishu"
```

Do **NOT** attempt to send generated .docx files back via QQ send_message — it silently drops the attachment.

### Recommended approach: Offer 3 options

Present the user with a clear choice instead of just saying "can't send":

1. **Upload to a temporary file sharing site** and give them a download link
2. **Tell the user the absolute path** on the server for SCP/SFTP download:
   > 文件已保存到: /home/admin/城乡规划考试资料/理论考试第五套（含答案）.docx
3. **Paste the full content as formatted text** directly in the chat (for shorter documents)

Use `clarify()` with these 3 options, or if the user seems technical, suggest option 2 with concrete paths. If they're not technical, prefer option 3 (paste content) or ask.

## 4. Adding Answers + Numbering (Common Task)

When the user asks "把答案填进去标序号":

- Parse the original docx to get the question text + answer key (usually at the end of the document under "参考答案")
- Build numbered question items: `1. Question text (A Answer)`
- For multiple-choice: write answer inline in parentheses
- For true/false: mark `✓` (U+2713) or `✗` (U+2717)
- Maintain the original section structure (单选题/多选题/判断题/论述题)
- Include the answer reference text for 论述题

## 5. Pitfalls

- **Two files in a row**: User may send theory paper first, then skill paper. Check both cached files — they're distinguished by content, not filename. Always parse both to identify which is which.
- **QQ filenames are lost**: The cache filename is a hash — the original filename from QQ is not preserved. You must infer from document content.
- **python-docx NOT in venv**: It installs to `~/.local`. Always use PYTHONPATH or install it into the hermes venv explicitly: `/opt/pipx/venvs/hermes-agent/bin/python -m pip install python-docx`
- **Chinese quotation marks in f-strings**: Avoid nesting Chinese curly quotes (""/「」) inside Python f-strings or triple-quoted strings. Use variables (e.g., `LB = "\u201c"`) and f-string interpolation instead.
- **Large documents**: docx.paragraphs iteration is fine for exam papers (50-100 paragraphs). For larger documents, consider reading only specific sections.
- **Avoid inline code for complex docx generation**: When generating .docx with Chinese text, special characters (curly quotes, em dashes, Unicode symbols like ✓✗①②), and many string literals, write the Python code to a `.py` file first with `write_file()`, then execute with `PYTHONPATH=... python3 script.py`. This avoids the shell escaping/quoting nightmare of triple-quoted heredocs or `-c` inline scripts. Example pattern:

  ```python
  # 1. Write the script
  write_file(path="/home/admin/gen_docs.py", content=script_content)
  
  # 2. Execute it with PYTHONPATH set
  terminal(f"PYTHONPATH=/home/admin/.local/lib/python3.12/site-packages python3 /home/admin/gen_docs.py")
  ```

- **Multiple cached documents**: When user sends multiple files in sequence, check BOTH cache entries. They're distinguished by content, not filename. Always parse all to identify which document is which.
