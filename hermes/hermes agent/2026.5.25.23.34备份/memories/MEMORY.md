User is running in WSL (Windows Subsystem for Linux). Windows host at /mnt/c/. Working directory: /mnt/c/Users/Administrator. Home: /home/after_ket.
§
DeepSeek models (including deepseek-v4-pro) cannot view images — vision_analyze returns "unknown variant 'image_url', expected 'text'". When the user sends images, ask them to describe the content or send URLs/links instead. Use curl to scrape website content as a fallback. See skill `model-fallbacks` for full degradation chain.
§
Galgame年鉴项目：桌面 galgame_catalog.html + images/ 文件夹。封面/背景/CG全部用 `images/xxx.jpg` 相对路径，而非 VNDB CDN（国内极慢10-25s/张）。分享给群友时打包ZIP发QQ群。音乐是 Web Audio API 合成的 BGM（8首和弦进行循环），无需MP3文件。VNDB封面API：POST api.vndb.org/kana/vn，search取image.url。参考站：青桔网/Hikarinagi/NekoGAL/稻荷GAL/月幕/Singureo/2DFan。
§
PC端和安卓端必须同步更新，双端联动。每次修改PC端时自动同步安卓端，一个bug两端一起修。galgame_catalog.html 文件位于 C:\Users\Administrator\Desktop\。
§
永久还原原点（已更新）：当前 galgame_catalog.html 版本 — 7主题色(暗/粉/金/绿/海/午夜/亮) + 15部游戏 + SummerPockets背景 + 8首音乐 + 烟花特效 + 留言板(localStorage) + 紫色友情卡片 + 双端适配。此后所有"还原"指令均以此版为第一还原点。
§
Galgame年鉴项目：每次修改 galgame_catalog.html 后必须更新 Desktop/galgame_versions/2026.5.21.1.29_原点版本/更新日志.txt，记录格式为【YYYY.M.D 更新记录】+ emoji条目。桌面文件和版本文件夹需保持同步。用户会检查是否记录。完整流程见技能 galgame-version-update。
§
用户偏好"不要一根筋"——某个方法行不通时快速换思路，不要反复尝试同一种方法。上传文件到CDN行不通就换Web Audio合成BGM，VNDB搜不到就换日文/英文名再搜。
§
WSL2代理：Clash Verge TUN模式，API端口9097。排查：PowerShell netstat确认 → Clash API(/configs) → TUN兜底。详见 wsl-proxy 技能。
§
用户喜欢义妹生活（三河Ghost/Hiten）和妹妹人生（入间人间/フライ）等深度心理描写的轻小说。偏好灵活快速切换方案——某个方法不行立刻换思路，不要一根筋反复尝试。
§
API中转站（/home/admin/api-relay/）：Flask 8848端口。支持 OpenAI /v1/chat/completions + Anthropic /v1/messages（非流式+流式SSE）。认证：Bearer / x-api-key。模型：deepseek-chat/reasoner、siliconflow-deepseek、sensenova-*、qwen/*（百炼通配）。令牌 sk-local-apirelay-2026。详细：api-relay skill。
§
上下文压缩摘要不可全信：之前一次会话的compaction摘要声称"用户要求清除项目"，但实际上那是在普拉娜roleplay情境下的误解——用户并未要求删除API中转站。当摘要内容与用户当前说法冲突时，以用户为准，不要死守摘要。
§
云端主力已完全重建：ECS 47.108.235.219，admin。Hermes网关+mihomo代理(7897)+API中转站(8848)均systemd自启。GitHub(xinghailiuli)+5sim($1.94)已配。7个cron：中转站/Hermes备份、早晚播报、Galgame速报、轻小说速报、健康监控。中转站6模型含百炼通配。本地WSL网关已停。API中转站文件~/api-relay/，server.py用系统python3+flask。
§
test