---
name: qq-stickers
description: 管理并发送二次元表情包。从用户获取图片、存储到本地库、在QQ对话中用MEDIA发送。
category: qq
---

# QQ 表情包管理

## 触发条件
- 用户要求发送表情包、图片表情、二次元表情
- 用户批量发送图片让你收藏
- 聊天中遇到适合用表情包回应的场景

## 表情包仓库
- 本地路径: `/home/admin/stickers/`
- GitHub备份: `hermesAI-backup/表情包/` (第二层级，非嵌套)
- 库存: 336张，格式 jpg/png/gif

## 发送方式
在 QQ 回复中使用 `MEDIA:/home/admin/stickers/文件名` 嵌入图片。

## 场景匹配
根据对话情绪选择合适的表情包：
- 开心/得意 → happy, cheerful 类
- 害羞/脸红 → blush, shy 类
- 生气/不满 → angry 类
- 惊讶/无语 → surprised, speechless 类
- 委屈/哭 → cry, sad 类
- 自嘲/吐槽 → 带文字的梗图类

## 添加新表情包
用户发来的图片缓存在 `/home/admin/.hermes/image_cache/`，复制到 stickers 目录即可：
```bash
cp /home/admin/.hermes/image_cache/img_xxx.jpg /home/admin/stickers/
```

## 备份到GitHub
```bash
cp /home/admin/stickers/* /home/admin/hermesAI-backup/表情包/
cd /home/admin/hermesAI-backup && git add 表情包/ && git commit -m "表情包更新" && git push
```

## 注意事项
- 不要自己画图生成表情包，只用现成的二次元图片
- 用户对表情包质量要求高，不是普通 emoji 或粗制滥造的图
- GitHub 备份时放第二层级（如 `表情包/`），不要嵌套到第三层级