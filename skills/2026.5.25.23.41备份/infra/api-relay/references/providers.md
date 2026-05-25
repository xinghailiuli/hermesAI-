# LLM Provider 接入速查

## 百炼 / DashScope（阿里云）

- **注册**: https://bailian.console.aliyun.com → 阿里云账号登录 → 模型广场开通服务 → API-KEY管理
- **Base URL**: `https://dashscope.aliyuncs.com/compatible-mode/v1`
- **环境变量**: `DASHSCOPE_API_KEY`
- **免费额度**: 100万 Token/月
- **模型数**: 244+（通义千问全系列 + DeepSeek + Kimi + GLM + MiniMax + 硅基流动等第三方）
  - **可用聊天模型**: ~166（过滤掉 TTS/ASR/图像/实时翻译/多模态实时等 78 个非聊天模型）
  - **过滤关键词**: `tts`, `asr`, `speech`, `realtime`, `image`, `wan`, `livetranslate`, `mt-`, `ocr`, `omni`, `gui`, `audio`, `vc-`, `vd-`, `s2s`, `xiaomi`, `vanchin`
  - `/v1/models/dashscope` 返回已过滤+分类的列表，每个模型带 `_cat` 分类字段
- **关键模型ID**: `qwen3.7-max`, `qwen3-max`, `qwen-plus`, `qwen-turbo`, `qwen-coder-plus`, `deepseek-v3.2`, `deepseek-v4-pro`, `kimi-k2.6`, `glm-5.1`
- **特殊**: 采用通配路由，任意传模型ID即可，无需在config.json逐个录入

## 豆包 / Doubao（火山引擎）

- **注册**: https://console.volcengine.com/ark → 火山引擎账号 → 模型推理 → 开通豆包 → 创建API Key
- **Base URL**: `https://ark.cn-beijing.volces.com/api/v3`
- **环境变量**: `DOUBAO_API_KEY`
- **免费额度**: 50万 Token/天
- **模型ID**: `doubao-lite-128k`, `doubao-pro-128k`

## 智谱 / ZhipuAI

- **注册**: https://open.bigmodel.cn → 注册 → API Keys
- **Base URL**: `https://open.bigmodel.cn/api/paas/v4`
- **环境变量**: `ZHIPU_API_KEY`
- **免费额度**: 注册即送
- **模型ID**: `glm-4-flash`, `glm-4-plus`

## 硅基流动 / SiliconFlow

- **注册**: https://siliconflow.cn → 注册 → API密钥
- **Base URL**: `https://api.siliconflow.cn/v1`
- **环境变量**: `SILICONFLOW_API_KEY`
- **模型ID**: `deepseek-ai/DeepSeek-V3`

## DeepSeek 官方

- **Base URL**: `https://api.deepseek.com/v1`
- **环境变量**: `DEEPSEEK_API_KEY`
- **模型ID**: `deepseek-chat`, `deepseek-reasoner`

## 日日新 / SenseNova Token Plan（商汤）

- **注册**: https://www.sensenova.cn/token-plan → 公测免费 → 创建 API Key（最多20个）
- **Base URL**: `https://token.sensenova.cn/v1`（⚠️ **不是** `api.sensenova.cn`，**不是** `/v1/llm`）
- **环境变量**: `SENSENOVA_API_KEY`
- **免费额度**: 公测期完全免费
  - `sensenova-6.7-flash-lite`: 1500次/5h（多模态智能体）
  - `sensenova-u1-fast`: 1500次/5h（信息图生成，可能需单独开通）
  - `deepseek-v4-flash`: 150次/5h（DeepSeek 高性能）
- **模型ID 格式**: 全小写 + 连字符，如 `sensenova-6.7-flash-lite`、`deepseek-v4-flash`
- **特殊处理**:
  1. Flash-Lite 的回复在 `reasoning` 字段而非 `content` → 中转站需映射 `reasoning → content`
  2. DeepSeek V4 Flash 需传 `"thinking": {"type": "disabled"}` 才能出正常文本（中转站自动注入）
  3. Flash-Lite 先思考再回答，需要 ≥500 max_tokens
- **Key 格式**: `sk-` 开头，与 DeepSeek/豆包 Key 格式相同，测试时容易混淆
