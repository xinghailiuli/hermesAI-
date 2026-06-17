# Multi-Instance Hermes Awareness

## Problem
When two Hermes instances (e.g., cloud server + local WSL) connect to the same messaging platform (QQ Bot, Telegram, etc.), the platform routes messages unpredictably:
- If both are online, either can receive the message
- The agent may believe it's on instance A but actually be on instance B
- This leads to wrong assumptions about network access, file paths, and capabilities

## Detection
At the start of EVERY session or when the user mentions "本地"/"云端"/"服务器", verify identity:

```bash
whoami && hostname && curl -s --noproxy '*' ifconfig.me && uptime
```

## Known Instances

| Instance | IP | Hostname | User | Data Path | Network |
|----------|-----|----------|------|-----------|---------|
| Cloud | 47.108.235.219 | iZ2vc1r6idxmchd2xcvb18Z | admin | /home/admin/.hermes/ | Alibaba CDN proxy, no adult/social sites |
| Local WSL | 171.218.193.32 | xinghailiuli | after_ket | ~/.hermes/ | User's Clash, all sites OK |

## Behavior
- Cloud is the primary/authoritative instance
- Local is secondary, used for tasks requiring user's network (iwara, YouTube, etc.)
- When user says "回到云端" or "用云端的", remind them to stop local WSL Hermes so QQ routes to cloud
