# QQ 图片生成与发送

## 适用场景

在 QQ 平台上通过 Hermes 生成并发送图片（表情包、示意图等）。

## 技术栈

- **Pillow (PIL)** — Python 图像生成库
- **MEDIA:路径** — Hermes 消息中的媒体文件标记，QQ 原生接收为图片

## 安装

Pillow 需安装到 Hermes 的 venv 中（`execute_code` 沙箱没有 Pillow）：

```bash
sudo /opt/pipx/venvs/hermes-agent/bin/python3 -m pip install Pillow \
  -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**注意**：普通 `pip install` 可能装到系统 Python，需明确用 Hermes venv 的 python3。

## 发送现成图片（表情包）- 推荐方式

**用户明确偏好：优先使用已有的二次元表情包/贴纸，不要自己画。**

### 从图站下载

Safebooru（safebooru.org）在中国大陆可直接访问，提供大量动漫反应图：

```bash
# 搜索标签，获取图片直链
curl -s "https://safebooru.org/index.php?page=dapi&s=post&q=index&tags=blush+rating:safe&limit=2" \
  | grep -oP 'file_url="[^"]+"'

# 下载到本地表情包目录
wget -q -O ~/stickers/blush.gif "https://safebooru.org/images/..."
```

常用标签：`blush`（害羞）、`angry`（生气）、`happy`（开心）、`crying`（大哭）、`surprised`（惊讶）、`smile`（微笑）

### 发送方式

```bash
# 消息中包含 MEDIA: 路径即可
MEDIA:/home/admin/stickers/blush.gif
```

## Pillow 生成（仅在无现成图时使用）

```python
# 在 terminal 中直接运行 Python（非 execute_code）
python3 << 'EOF'
from PIL import Image, ImageDraw, ImageFont

img = Image.new('RGBA', (400, 400), (255, 255, 255, 0))
draw = ImageDraw.Draw(img)
# ... 绘制内容 ...
img.save("/tmp/output.png")
print("MEDIA:/tmp/output.png")  # 这行输出会被 Hermes 识别为媒体附件
EOF
```

**关键**：脚本最后一行 `print("MEDIA:/absolute/path")` 是触发图片发送的标记。

## 中文文字支持

```python
# 查找可用中文字体
import matplotlib.font_manager
# 或直接指定已知字体路径
font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", 24)
```

如果系统无中文字体，可安装：
```bash
sudo apt-get install fonts-noto-cjk
```

## Pitfalls

- `execute_code` 沙箱没有 Pillow，必须用 `terminal` 运行
- 权限问题：Hermes venv 在 `/opt/pipx/` 下，需 `sudo`
- 图片路径必须是绝对路径
- PNG 支持透明通道（RGBA），生成的背景可设为透明
