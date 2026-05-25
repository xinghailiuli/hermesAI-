---
name: api-relay
description: Build and maintain a local API relay server that aggregates multiple LLM providers (DeepSeek, 百炼/DashScope, 硅基流动, 豆包, 智谱, etc.) under a single OpenAI-compatible endpoint.
---

# API 中转站

## 项目位置

`~/api-relay/` — Flask + OpenAI 兼容接口，监听 `127.0.0.1:8848`

## 从零重建

如果中转站文件丢失（服务器重置、迁移遗漏等），可从技能模板重建。

### 前置：安装 Flask（国内/Ubuntu 24.04）

**Ubuntu 24.04 PEP 668 阻断系统 pip**，必须加 `--break-system-packages`。国内服务器走代理：

```bash
export HTTP_PROXY=http://127.0.0.1:7897 HTTPS_PROXY=http://127.0.0.1:7897
pip3 install flask requests --break-system-packages
```

不用 mihomo 代理则 pip 超时；不加 `--break-system-packages` 则被 PEP 668 拦截。

pipx 的 hermes venv（`/opt/pipx/venvs/hermes-agent/`）不含 pip，不能用 `~/hermes_env/bin/pip`。

### 部署文件

```bash
mkdir -p ~/api-relay
cp ~/.hermes/skills/infra/api-relay/templates/server.py ~/api-relay/
cp ~/.hermes/skills/infra/api-relay/templates/config.json ~/api-relay/
cp ~/.hermes/skills/infra/api-relay/templates/dashboard.html ~/api-relay/
cp ~/.hermes/skills/infra/api-relay/templates/requirements.txt ~/api-relay/
# 安装依赖并启动（见下方「持久运行」节）
```

如果模板不存在，用 `skill_manage action=write_file` 写入模板到 `templates/` 目录。

⚠️ `hermes backup` 只打包 `~/.hermes/`，**不包含 `~/api-relay/`**。务必单独备份中转站或使用 cron 每日备份。

## 文件结构

```
~/api-relay/
  server.py          # Flask 服务主程序
  config.json        # 模型配置（固定模型列表）
  dashboard.html     # 控制面板前端
  requirements.txt   # flask, requests
  start.sh           # 启动脚本
  test.py            # 测试脚本
```

## 配置模型 (config.json)

```json
{
  "server": {"host": "127.0.0.1", "port": 8848, "debug": false},
  "auth": {
    "local_token": "sk-local-apirelay-2026",
    "require_auth": true,
    "_note": "Supports Authorization: Bearer + x-api-key headers"
  },
  "models": [
    {
      "id": "模型ID（用户调用时传的model参数）",
      "name": "显示名称",
      "provider": "deepseek|qwen|doubao|zhipu|siliconflow",
      "base_url": "上游API的base URL（到/v1级别）",
      "model": "上游实际模型名",
      "enabled": true
    }
  ],
  "api_keys": {
    "deepseek": "DEEPSEEK_API_KEY",
    "qwen": "DASHSCOPE_API_KEY",
    "doubao": "DOUBAO_API_KEY",
    "zhipu": "ZHIPU_API_KEY",
    "siliconflow": "SILICONFLOW_API_KEY"
  }
}
```

## 百炼通配路由（核心模式）

百炼(DashScope)提供 244+ 模型，不可能逐个录入 config.json。server.py 的 `get_model_config()` 实现了自动回退：

1. 先在 `config.json` 的 models 列表中查找
2. 未匹配时，如果 `DASHSCOPE_API_KEY` 已设置 → 自动生成虚拟配置，转发到 `https://dashscope.aliyuncs.com/compatible-mode/v1`
3. 用户传任意百炼模型ID即可直接调用

```python
def get_model_config(model_id):
    for m in CONFIG['models']:
        if m['id'] == model_id and m['enabled']:
            return m
    # 百炼通配回退
    if DASHSCOPE_KEY:
        return {
            'id': model_id,
            'provider': 'dashscope',
            'base_url': DASHSCOPE_BASE,
            'model': model_id,
            'enabled': True,
            '_passthrough': True
        }
    return None
```

## 添加新 Provider

1. 在 `config.json` 的 `api_keys` 中注册环境变量名映射
2. 在 `config.json` 的 `models` 中添加模型条目
3. 将 API Key 写入 `~/.hermes/.env`
4. 如需通配路由（模型数量多），在 `get_model_config()` 和 `get_upstream_key()` 中添加回退逻辑
5. 重启服务

## 启动与重启

```bash
# 停止旧进程
kill $(pgrep -f "python.*server.py") 2>/dev/null

# 启动（必须带所有环境变量）
cd ~/api-relay && \
  set -a && source ~/.hermes/.env && set +a && \
  python3 server.py
```

环境变量从 `~/.hermes/.env` 读取。

## 持久运行（systemd 服务）

中转站不会自动重启，进程挂了或系统重启后需要手动拉起来。用 systemd 服务保活：

**用户级服务**（推荐，无需 sudo）：

```bash
mkdir -p ~/.config/systemd/user

cat > ~/.config/systemd/user/api-relay.service << 'EOF'
[Unit]
Description=API Relay Server
After=network-online.target

[Service]
Type=simple
WorkingDirectory=%h/api-relay
EnvironmentFile=%h/.hermes/.env
Environment=HTTP_PROXY=http://127.0.0.1:7897
Environment=HTTPS_PROXY=http://127.0.0.1:7897
Environment=http_proxy=http://127.0.0.1:7897
Environment=https_proxy=http://127.0.0.1:7897
Environment=NO_PROXY=localhost,127.0.0.1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16,.local,.internal
ExecStart=/usr/bin/python3 %h/api-relay/server.py
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now api-relay
```

需要 linger 才能让用户服务在未登录时运行：
```bash
sudo loginctl enable-linger $USER
```

**检查状态**：
```bash
systemctl --user status api-relay
curl http://127.0.0.1:8848/health
```

**没有 systemd 时**（Docker 容器等），用 cron 兜底：
```
* * * * * pgrep -f "python.*server.py" || (cd ~/api-relay && set -a && . ~/.hermes/.env && set +a && python3 server.py &)
```

## 云服务器部署

中转站部署到云服务器后可 24 小时在线。只需：
1. 把 `~/api-relay/` 整个目录 scp 到服务器
2. 服务器上创建 `~/.hermes/.env` 写入同样的 API 密钥
3. 配好 systemd 服务（同上）
4. 确保安全组开放 8848 端口（或通过 Nginx 反代）

注意：8848 只监听 `127.0.0.1`，外网访问需改为 `0.0.0.0` 或在 config.json 中调整 `server.host`。

## 测试

```bash
# 健康检查
curl http://127.0.0.1:8848/health

# OpenAI 模型列表
curl http://127.0.0.1:8848/v1/models \
  -H 'Authorization: Bearer sk-local-apirelay-2026'

# OpenAI 聊天
curl http://127.0.0.1:8848/v1/chat/completions \
  -H 'Authorization: Bearer sk-local-apirelay-2026' \
  -H 'Content-Type: application/json' \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"hi"}],"max_tokens":20}'

# Anthropic Messages（非流式）
curl -s -X POST http://localhost:8848/v1/messages \
  -H "x-api-key: sk-local-apirelay-2026" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","max_tokens":50,"messages":[{"role":"user","content":"Hello"}],"stream":false}'

# Anthropic Messages（流式 SSE）
curl -s -N -X POST http://localhost:8848/v1/messages \
  -H "x-api-key: sk-local-apirelay-2026" \
  -H "Content-Type: application/json" \
  -d '{"model":"deepseek-chat","max_tokens":50,"messages":[{"role":"user","content":"Hello"}],"stream":true}'
```

## Anthropic Messages API（/v1/messages）

中转站支持 Anthropic Messages API 端点，使 Claude Code 等 Anthropic 客户端
能通过中转站使用 DeepSeek 等 OpenAI 兼容后端。

- 端点：`POST /v1/messages`
- 认证：支持 `x-api-key` 和 `Authorization: Bearer`
- 模型映射：Claude 模型名在请求处理中直接映射到 `deepseek-chat`（`config.json` 的 `anthropic_model_map` 也支持但非必需）
- 详细文档：`references/anthropic-translation.md`

**Claude Code 环境变量**：
```bash
export ANTHROPIC_BASE_URL="http://localhost:8848"        # ⚠️ 不要加 /v1！
export ANTHROPIC_API_KEY="sk-local-apirelay-2026"
```

### 关键 Pitfalls

**`ANTHROPIC_BASE_URL` 不要带 `/v1`**：Claude Code 内部自动追加 `/v1/messages`。若
base URL 设为 `http://localhost:8848/v1`，实际请求变成 `POST /v1/v1/messages` → 405。

**Claude 模型名必须显式映射**：`get_model_config()` 的通配回退会将未知模型名路由到 DashScope
passthrough，导致 DeepSeek 收到不存在的模型名返回空响应。修复：在 `anthropic_messages()`
开头加入 Claude→DeepSeek 直接映射：
```python
if 'claude' in model_id.lower() or 'anthropic' in model_id.lower():
    model_id = 'deepseek-chat'
```

**npm 原生二进制安装**：Claude Code 的 `@anthropic-ai/claude-code-linux-x64` 原生包在
淘宝镜像上缺失，需切回 npm 官方源 + 代理下载：
```bash
npm config set registry https://registry.npmjs.org/
npm config set proxy http://127.0.0.1:7897
npm config set https-proxy http://127.0.0.1:7897
```

## 各 Provider 注册地址

| Provider | 注册地址 | 免费额度 |
|----------|---------|---------|
| 百炼 (DashScope) | bailian.console.aliyun.com | 100万T/月 |
| 日日新 (SenseNova) | sensenova.cn/token-plan | 公测免费，1500次/5h |
| 豆包 (Doubao) | console.volcengine.com/ark | 50万T/天 |
| 智谱 (Zhipu) | open.bigmodel.cn | 注册即送 |
| 硅基流动 | siliconflow.cn | 送额度 |

## 仪表盘联动更新

修改模型列表后必须同步更新 dashboard：

1. **server.py `dashboard_stats`**：models_display 需包含通配模型（`_wildcard: True`）
2. **dashboard.html JS**：`_wildcard` 条目不渲染切换按钮，显示 `🌐 通配` 标签
3. **dashboard.html 令牌**：`Authorization: Bearer xxx` 必须与 `config.json` 的 `auth.local_token` 完全一致
4. 通配模型存在时，显示百炼模型列表入口链接

```javascript
// dashboard.html 中的模型渲染（处理 _wildcard）
${m._wildcard 
  ? '<span style="font-size:0.7rem;color:var(--blue)">🌐 通配</span>' 
  : `<button class="toggle ${m.enabled?'on':'off'}" onclick="toggleModel('${m.id}')">${m.enabled?'已启用':'已停用'}</button>`
}
```

## 百炼模型过滤与分类

百炼 `/v1/models` 返回 244 个模型，但大量是 TTS/ASR/图像/实时翻译等非聊天模型。直接全量展示会导致用户选中后 404。server.py 的 `/v1/models/dashscope` 端点做了过滤和分类：

**过滤关键词**（包含任一则剔除）：
`tts`, `asr`, `speech`, `realtime`, `image`, `wan`, `livetranslate`, `mt-`, `ocr`, `omni`, `gui`, `audio`, `vc-`, `vd-`, `s2s`, `xiaomi`, `vanchin`

过滤后约 166 个纯聊天模型，按分类组织：
- 🆕 最新旗舰 (qwen3.7, qwen3.6)
- ⭐ Qwen3.5
- 🤔 深度推理 (qwq, qvq, deep-research)
- 💻 代码编程 (coder)
- 📐 数学推理 (math)
- 🧠 Qwen3
- 🔍 DeepSeek
- 🌙 Kimi
- 🔥 智谱GLM
- 🎭 MiniMax
- 📦 经典系列 (qwen1/2/qwen-)
- 📦 其他

每个模型附加 `_cat` 字段。dashboard 子菜单用 `<optgroup label="分类名">` 分组展示，按推荐顺序排列（旗舰→推理→编程→…→经典→其他）。

```javascript
// dashboard.html loadDashscopeModels() 中的分组渲染
const catOrder = ['🆕 最新旗舰','⭐ Qwen3.5','🤔 深度推理',...];
const sorted = [...models].sort((a,b) => {
  const ca = catOrder.indexOf(a._cat), cb = catOrder.indexOf(b._cat);
  return (ca==-1?99:ca) - (cb==-1?99:cb) || a.id.localeCompare(b.id);
});
for (const m of sorted) {
  if (m._cat !== lastCat) {
    if (lastCat) html += '</optgroup>';
    html += `<optgroup label="${m._cat}">`;
    lastCat = m._cat;
  }
  html += `<option value="${m.id}">${m.id}</option>`;
}
```

## Pitfalls

### 中转站进程消失
中转站不会自动重启。重启 WSL 或进程崩溃后 `curl 8848` 无响应。用 `ps aux | grep relay` 确认进程存活，如果不在就用 systemd/cron 保活（见「持久运行」节）。

### 百炼通配模型 404
大部分原因是选到了非聊天模型（TTS、ASR、图片生成等）。解决方案：用 `/v1/models/dashscope`（已过滤）代替全量列表，或在通配子菜单中只展示聊天模型。如果在其他客户端直接用 model ID 调用，先确认模型支持 chat completions。

### SenseNova (日日新) Token Plan — 完整配置

**正确端点**：`https://token.sensenova.cn/v1`（⚠️ 不是 `api.sensenova.cn`，不是 `/v1/llm`）

**正确模型 ID**（全小写，连字符分隔）：
- `sensenova-6.7-flash-lite` — 多模态智能体，1500次/5h
- `sensenova-u1-fast` — 信息图生成，1500次/5h（可能需额外开通）
- `deepseek-v4-flash` — DeepSeek 高性能，150次/5h

**Key 测试流程**：
1. 先测 `https://token.sensenova.cn/v1/chat/completions`（正确端点）
2. 先测 `deepseek-v4-flash` 模型（最容易通）
3. 不要用 `api.sensenova.cn` 或 `/v1/llm` 路径！

**SenseNova 特有处理（server.py 必须实现）**：

```python
# 1. Flash-Lite 把回复放在 reasoning 字段而非 content → 需映射
for choice in result.get('choices', []):
    msg = choice.get('message', {})
    if not msg.get('content') and msg.get('reasoning'):
        msg['content'] = msg.pop('reasoning')

# 2. DeepSeek V4 Flash 需关闭思考模式才能输出正常 content
if provider == 'sensenova' and 'deepseek' in model_name:
    if 'thinking' not in payload:
        payload['thinking'] = {'type': 'disabled'}
```

**Flash-Lite 注意**：模型先思考再回答，需要足够的 max_tokens（建议 ≥500），否则只返回思考过程被截断。

### 未知 Key 平台识别流程
用户提供 Key 但不说平台时，按以下顺序批量测试：
1. 豆包 (`ark.cn-beijing.volces.com`) → 智谱 → 硅基流动 → DeepSeek官方 → 百炼 → Kimi → Groq → StepFun → 零一万物 → 日日新
2. 全部失败则用 `clarify` 询问用户
3. "Forbidden" 但非 "Unauthorized" = Key有效但权限不足（常见于日日新）

### 豆包 Key 格式
`sk-` 开头。豆包用 `ep-` 前缀的是 endpoint ID 而非 API Key。若返回 "The API key format is incorrect" 则不是豆包 Key。

### 仪表盘聊天静默失败
dashboard.html 的 `sendChat()` 中硬编码了 `Authorization: Bearer sk-xxx`。若与控制台令牌不一致，聊天请求返回 401 但前端无明确提示。

### 仪表盘 3秒刷新冲掉下拉选择
`setInterval(load, 3000)` 每次重建 `<select>` 的 innerHTML 导致选中项复位。修复：
```javascript
const sel = document.getElementById('chatModel');
const prevVal = sel.value;
sel.innerHTML = ...;
if (prevVal) sel.value = prevVal;
onModelChange();  // 恢复联动（如通配子菜单）
```

### 百炼通配模型选择 UX
选中 `qwen/*` 通配条目时，需弹出一个子 `<select>` 加载全部 244 个 DashScope 模型供选择：
```javascript
function onModelChange() {
  if (sel.value === 'qwen/*') {
    ws.style.display = 'block';
    if (ws.options.length <= 1) loadDashscopeModels();  // 懒加载
  } else {
    ws.style.display = 'none';
  }
}
async function loadDashscopeModels() {
  const r = await fetch('/v1/models/dashscope',
    {headers: {'Authorization': 'Bearer sk-local-apirelay-2026'}});
  // 填充 ws.innerHTML...
}
```
发送时取子菜单的 value 作为实际 model ID。

### 从零重建中转站

中转站文件丢失时，按以下步骤重建：

**1. 前提：代理必须已运行**

```bash
curl -x http://127.0.0.1:7897 -sI https://github.com | head -1  # 确认 200
```

**2. 安装 Flask（Ubuntu 24.04 注意 PEP 668）**

```bash
export HTTP_PROXY=http://127.0.0.1:7897 HTTPS_PROXY=http://127.0.0.1:7897
pip3 install flask requests --break-system-packages
```

⚠️ Ubuntu 24.04 系统级 pip 被 PEP 668 保护，必须加 `--break-system-packages`。不走代理则 pip 超时（exit code 124）。

**3. 文件部署**

通过 write_file 本地写好 → scp 上传，避免 heredoc 转义地狱：

```bash
# 本地写 server.py / config.json / dashboard.html
write_file /tmp/api-relay-files/server.py → scp 到云端 ~/api-relay/
```

必需文件：`server.py` | `config.json` | `dashboard.html` | `requirements.txt`

**4. 创建 systemd 服务**

必须同时注入 `.env` 密钥和 `HTTP_PROXY/HTTPS_PROXY` 环境变量。中转站调用上游 API 时需要代理（DeepSeek 直连通，但硅基流动等可能不走代理连不上）。

```bash
cat > ~/.config/systemd/user/api-relay.service << 'EOF'
[Unit]
Description=API Relay Server
After=network-online.target
[Service]
Type=simple
WorkingDirectory=%h/api-relay
EnvironmentFile=%h/.hermes/.env
Environment=HTTP_PROXY=http://127.0.0.1:7897
Environment=HTTPS_PROXY=http://127.0.0.1:7897
ExecStart=/usr/bin/python3 %h/api-relay/server.py
Restart=always
RestartSec=5
[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload
systemctl --user enable --now api-relay
```

**5. 验证**

```bash
curl http://127.0.0.1:8848/health                          # {"status":"ok"}
curl http://127.0.0.1:8848/v1/chat/completions \
  -H 'Authorization: Bearer sk-local-apirelay-2026' \
  -H 'Content-Type: application/json' \
  -d '{"model":"deepseek-chat","messages":[{"role":"user","content":"hi"}],"max_tokens":20}'
```
