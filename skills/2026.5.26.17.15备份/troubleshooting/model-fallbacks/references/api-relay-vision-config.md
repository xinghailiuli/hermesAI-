# API Relay + DashScope 视觉模型配置

## 适用场景

DeepSeek 等不支持图片的模型，通过已有 API 中转站路由到阿里百炼的视觉模型。

## 前提条件

- API 中转站已配置 DashScope 通配（`qwen/*`）
- DashScope API key 有效且余额充足
- 中转站运行在 `127.0.0.1:8848`

## Hermes 配置

### 辅助视觉模型

```bash
hermes config set auxiliary.vision.provider "custom:apirelay"
hermes config set auxiliary.vision.model "qwen-vl-plus"
hermes config set auxiliary.vision.base_url "http://127.0.0.1:8848/v1"
hermes config set auxiliary.vision.api_key "sk-local-apirelay-2026"
```

### 注册自定义 Provider

在 `~/.hermes/config.yaml` 的 `providers` 段添加：

```yaml
providers:
  apirelay:
    base_url: http://127.0.0.1:8848/v1
    api_key: sk-local-apirelay-2026
    model: qwen-vl-plus
```

## 效果

```
用户发图 → vision_analyze → API中转站 → 百炼 qwen-vl-plus → 返回分析文字
```

DeepSeek 自己看不到图，但 Hermes 自动把图片请求路由给 qwen-vl-plus 处理，结果无缝返回。

## 模型限制

- 图片最小尺寸：10×10 像素（DashScope qwen-vl-plus 要求）
- 支持的格式：PNG、JPEG、WEBP、GIF（非动图）
- 图片大小：建议 < 20MB

## 替代方案（本地）

[hermes-local-vision](https://github.com/growwithsmc/hermes-local-vision) 提供本地 VLM（Qwen2.5-VL-7B via llama.cpp），但需要 GPU。CPU 推理需要 8GB+ 内存。轻量 ECS（如 1.6GB RAM 阿里云实例）不适合。

## 测试流程

```bash
# 1. 确认中转站健康
curl -s 127.0.0.1:8848/health

# 2. 测试视觉模型（发送 20×20 红色测试图）
python3 -c "
import base64, struct, zlib, json, urllib.request
def chunk(c,d):return struct.pack('>I',len(d))+c+d+struct.pack('>I',zlib.crc32(c+d)&0xffffffff)
raw=b'\x00'+bytes([255,0,0])*400
png=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',20,20,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(raw))+chunk(b'IEND',b'')
b64=base64.b64encode(png).decode()
req=urllib.request.Request('http://127.0.0.1:8848/v1/chat/completions',
  data=json.dumps({'model':'qwen-vl-plus','messages':[{'role':'user','content':[{'type':'text','text':'什么颜色？'},{'type':'image_url','image_url':{'url':f'data:image/png;base64,{b64}'}}]}],'max_tokens':10}).encode(),
  headers={'Authorization':'Bearer sk-local-apirelay-2026','Content-Type':'application/json'})
print(json.loads(urllib.request.urlopen(req,timeout=15).read())['choices'][0]['message']['content'])
"
# 预期输出：红色

# 3. 重启网关使配置生效
hermes gateway restart
```
