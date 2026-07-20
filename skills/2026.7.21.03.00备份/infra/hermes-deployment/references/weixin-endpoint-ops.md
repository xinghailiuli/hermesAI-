# 微信端点运维操作

## 快速状态检查

```bash
# 查看最近微信日志
grep -i -E "weixin|wechat" ~/.hermes/logs/gateway.log | tail -8
```

期望输出（在线）：
```
INFO gateway.run: Connecting to weixin...
INFO gateway.platforms.weixin: [Weixin] Connected account=5b140324 base=https://ilinkai.weixin.qq.com
INFO gateway.run: ✓ weixin connected
```

## 微信连接信息

| 项目 | 详情 |
|------|------|
| 接入方式 | HTTPS 出站连接 |
| 接入点 | `https://ilinkai.weixin.qq.com` |
| 账号格式 | `<id>@im.bot` |
| 用户格式 | `<openid>@im.wechat` |
| 频道类型 | DM（私聊） |

## 微信账号配置

账号配置存储在 `~/.hermes/weixin/accounts/<account_id>.json`：

```json
{
  "token": "<id>@im.bot:<secret>",
  "base_url": "https://ilinkai.weixin.qq.com",
  "user_id": "<openid>@im.wechat",
  "saved_at": "2026-05-27T12:53:40Z"
}
```

## 关键区别：微信 vs QQ

| 维度 | 微信 | QQ |
|------|------|------|
| 协议 | HTTPS 轮询/长连接 | WebSocket 长连接 |
| 接入点 | ilinkai.weixin.qq.com | api.sgroup.qq.com/wss |
| 本地监听端口 | 无（出站连接） | 无（出站连接） |
| Token 刷新 | 按需 | 定时（~1500s 过期） |
| Session 管理 | 无显式 session | 有 Ready + session_id |

## 会话记录

### 2026-05-27 20:58 — 微信/QQ 端口查询

- 用户查看网关的微信和QQ端口状态
- 使用 `hermes status` 确认两个平台均在线
- 微信通过 HTTPS 连接 `ilinkai.weixin.qq.com`，QQ 通过 WebSocket 连接 `api.sgroup.qq.com`
- 两者均为出站连接，无本地监听端口
