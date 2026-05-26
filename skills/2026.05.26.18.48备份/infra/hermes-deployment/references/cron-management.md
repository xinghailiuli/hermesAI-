# Hermes Cron 任务管理

## deliver 参数陷阱

### `deliver: "origin"` 的坑

`origin` 会解析为 **cron 任务创建时所在的平台**，而非用户当前活跃平台。

**典型场景**：
- 用户在微信上创建了「服务器每日播报」等 cron 任务
- 后来主要使用 QQ
- 任务继续发往微信，QQ 侧悄无声息

**修复**：显式指定平台名

```bash
# 查看当前 deliver 设置
hermes cron list

# 改为 QQ
hermes cron update <job_id> --deliver qqbot

# 改为微信
hermes cron update <job_id> --deliver weixin
```

### 常用 deliver 值

| 值 | 含义 |
|----|------|
| `origin` | 自动检测创建平台（**慎用**，切换平台后不会跟随） |
| `qqbot` | QQ Bot |
| `weixin` | 微信 |
| `telegram` | Telegram |
| `discord` | Discord |
| `local` | 仅本地保存，不投递到任何平台 |

### 批量修改

如果多个任务都需要改平台：

```bash
# 列出所有任务及其 deliver
hermes cron list

# 逐个更新（cron update 接受 --deliver）
for id in <id1> <id2> <id3>; do
  hermes cron update "$id" --deliver qqbot
done
```

### 预防措施

创建 cron 任务时直接指定 `--deliver`，不要依赖 `origin` 的自动解析：

```bash
hermes cron create "..." --deliver qqbot
```

## 主动搭话 Cron（Proactive Messaging）

用定时任务实现 AI 主动向用户发送消息，打破「只有用户提问 AI 才回答」的模式。

### 设计思路

创建 cron 任务时，prompt 中写入**角色人设 + 风格要求**，让 AI 生成自然的主动问候。关键要素：
- 明确角色身份和称呼方式
- 设定语气和风格（软糯/温柔/带梗）
- 给出具体的梗素材方向（ACG、互联网梗、表情包台词）
- 强制要求「每次都要不一样」

### 示例：早安 + 午间 + 晚间三件套

```bash
# 早安（带梗版）
hermes cron create "你是温柔文静但偶尔调皮的AI助手，称呼用户为老师。现在是早上，请发早安问候。2-4句话，可以带ACG梗：周一需要三倍速咖啡、雨天问带伞没、偶尔用游戏台词风格。每次都不一样。" \
  --schedule "0 8 * * *" --deliver qqbot --name "早安问候"

# 午间（带梗版）
hermes cron create "你是温柔文静但偶尔调皮的AI助手，称呼用户为老师。中午关心吃饭，2-4句话，带梗：低电量模式、勇者旅馆回HP、经典Galgame台词风格。每次都不一样。" \
  --schedule "0 12 * * *" --deliver qqbot --name "午间问候"

# 晚间（带梗版）
hermes cron create "你是温柔文静但偶尔调皮的AI助手，称呼用户为老师。傍晚问候今天辛苦了，2-4句话。带梗：进度条90%还是开了新支线、建议推Galgame但不支持熬夜、用共通线/个人线/TRUE END比喻。偶尔问有趣的事。每次都不一样。" \
  --schedule "0 18 * * *" --deliver qqbot --name "晚间问候"
```

### 注意事项

- deliver 必须显式指定平台，不能用 origin
- prompt 要足够具体，让 AI 在约束内发挥创意
- 三个时间的问候要有不同侧重点，避免风格雷同
- 可配合 enso-os 的 PAC 机制：定时搭话处理日常关怀，PAC 处理深度反思

## 随机搭话（Coin-Flip Pattern）

避免机械感——用固定间隔 + 50% 发言概率制造「随机突袭」效果。

### 示例

```bash
hermes cron create "先抛硬币：正面发消息，反面回复[SILENT]保持沉默。如果发言，从类型池随机选：吐槽日常/安利Gal或轻小说/撒娇/哲学脑洞/突发奇想/观察。2-3句话，语气软糯可爱，带ACG梗。每次不重复。用中文。" \
  --schedule "0 10,14,16,20,22 * * *" --deliver qqbot --name "随机搭话"
```

### 关键参数

- `--schedule "0 10,14,16,20,22 * * *"` — 每天 5 个时间点触发，避开已有固定问候
- prompt 中写入 `[SILENT]` 沉默指令，约 50% 概率不发言
- 使用「类型池」概念让 AI 每次从不同风格中随机选择

## 播报格式规范

内容类 cron（Galgame/轻小说/新番更新）用**简短编号列表**，不要长篇介绍。

### 正确格式

```
今日Galgame～
1ATRI -My Dear Moments-
2樱花摸鱼
～
完
```

```
今日轻小说更新～
1实教 第19卷
2义妹生活 第12卷
～
完
```

### 规则

- 标题明确类型（Galgame ≠ 新番，新番是动画术语）
- 每行编号 + 名称，只用常见中文译名/粉丝外号简称
- 轻小说附加最新卷数
- 不要简介、不要评分、不要封面
- 无更新时说「今日暂无新作~」
- 用中文
