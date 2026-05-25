# SiliconFlow Vision Model 30003 Error

## Error Signature

When `vision_analyze` routes to any SiliconFlow vision model, the API returns:

```
Error code: 403 - {'code': 30003, 'message': 'Model disabled.', 'data': None}
```

## Root Cause

SiliconFlow **requires manual enablement** of vision models per account. Even with a valid API key that works for text models (`deepseek-ai/DeepSeek-V3` etc.), vision models are **disabled by default** and return 30003 until the user explicitly enables them.

This is **fundamentally different** from DeepSeek's `unknown variant 'image_url'` error (400 bad request — model has no vision capability at all).

## Step-by-Step Fix

1. User logs into [siliconflow.cn](https://siliconflow.cn)
2. Navigate to **模型广场** (Model Marketplace)
3. Search for `VL` or `vision`
4. Click on a vision model (e.g., `Qwen/Qwen2.5-VL-72B-Instruct`)
5. Click **开通** (Enable) or **立即使用** (Use Now)
6. Once enabled, the model becomes available via API immediately — no restart needed

## Confirmed Disabled-By-Default Models

| Model | Status (May 2025) |
|-------|-------------------|
| `Qwen/Qwen2-VL-72B-Instruct` | Needs manual enable |
| `Qwen/Qwen2.5-VL-72B-Instruct` | Needs manual enable |
| `deepseek-ai/deepseek-vl2` | Needs manual enable |

## Hermes Config After Enablement

Once the user enables a vision model on SiliconFlow:

```bash
hermes config set auxiliary.vision.provider siliconflow
hermes config set auxiliary.vision.model Qwen/Qwen2.5-VL-72B-Instruct
```

## Degradation Rule

If the **first** SiliconFlow vision model returns 30003, **do not retry** other SiliconFlow VL models — they will all fail the same way. The entire vision category is disabled for that account. Immediately fall back to non-vision workarounds or suggest the user switch to a different vision provider (OpenRouter, Claude API, etc.).
