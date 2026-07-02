#!/usr/bin/env python3
"""
Codex WS Bridge — persistent WebSocket bridge for Codex CLI agent loop.
Logs to /tmp/codex_bridge.log
"""
import asyncio, json, uuid, os, re
import aiohttp
from aiohttp import web, WSMsgType
from datetime import datetime

LOG = open('/tmp/codex_bridge.log', 'a', buffering=1)
def log(msg):
    LOG.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")

FLASK_RELAY = "http://127.0.0.1:8847"
with open(os.path.join(os.path.dirname(__file__), 'config.json')) as f:
    AUTH = "Bearer " + json.load(f)['auth']['local_token']

async def ws_handler(request):
    log(f"WS connection from {request.remote}")
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    # Send session.created with model info (Codex expects this)
    await ws.send_json({
        "type": "session.created",
        "session": {
            "id": f"sess_{uuid.uuid4().hex[:24]}",
            "model": "deepseek-chat",
            "modalities": ["text"],
            "instructions": "",
            "tools": [],
            "tool_choice": "auto",
            "context_window": 128000,
            "max_output_tokens": 16384,
            "temperature": 0.7,
        }
    })
    
    conversation = []  # accumulate history for this session
    turn = 0
    
    try:
        async for msg in ws:
            if msg.type != WSMsgType.TEXT:
                log(f"WS non-text msg: {msg.type}")
                continue
            if msg.type == WSMsgType.CLOSE or msg.type == WSMsgType.ERROR:
                break
                
            turn += 1
            data = json.loads(msg.data)
            log(f"[turn {turn}] WS received: type={data.get('type')}, model={data.get('model')}, inp_preview={json.dumps(data.get('input',''), ensure_ascii=False)[:200]}")
            log(f"[turn {turn}] instructions len={len(data.get('instructions',''))}")
            
            model_id = data.get("model", "deepseek-chat")
            inp = data.get("input", "")
            instructions = data.get("instructions", "")
            
            # Build message: Codex puts everything in 'instructions' field
            # (system prompt + user message, 20K+ chars). 'input' field
            # may contain additional context (permissions, env info) on later turns.
            msg_content = instructions or ""
            
            # Append any extra input content
            if isinstance(inp, list):
                extra = []
                for item in inp:
                    if isinstance(item, dict):
                        c = item.get("content", "")
                        if isinstance(c, list):
                            c = "\n".join(
                                p.get("text","") for p in c
                                if isinstance(p,dict) and p.get("type") in ("text","input_text")
                            )
                        if c:
                            extra.append(c)
                    elif isinstance(item, str):
                        extra.append(item)
                if extra:
                    msg_content += "\n\n---\n" + "\n".join(extra)
            elif isinstance(inp, str) and inp:
                msg_content += "\n\n---\n" + inp
            
            if not msg_content:
                msg_content = "Hello"
            
            # Detect Chinese for language hint
            has_chinese = any('\u4e00' <= c <= '\u9fff' for c in msg_content)
            
            # Build conversation
            messages = []
            sys_hints = []
            if has_chinese:
                sys_hints.append("Respond in Chinese (Simplified).")
            sys_hints.append("When executing terminal commands, output ONLY a ```bash code block with the exact commands. No explanations, no markdown outside the code block. Keep output minimal.")
            messages.append({"role": "system", "content": " ".join(sys_hints)})
            messages.append({"role": "user", "content": msg_content})
            
            # Append previous assistant response for continuity
            if conversation:
                last = conversation[-1]
                messages = conversation[-2:] + messages[0:] if len(conversation) >= 2 else messages
            
            resp_id = f"resp_{uuid.uuid4().hex[:24]}"
            item_id = f"item_{uuid.uuid4().hex[:24]}"
            part_id = f"part_{uuid.uuid4().hex[:24]}"
            
            # Call upstream relay with full message
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{FLASK_RELAY}/v1/chat/completions",
                    headers={"Authorization": AUTH, "Content-Type": "application/json"},
                    json={
                        "model": model_id,
                        "messages": messages,
                        "max_tokens": data.get("max_output_tokens", 4096),
                        "temperature": data.get("temperature", 0.7),
                        "stream": False
                    },
                    timeout=aiohttp.ClientTimeout(total=180)
                ) as r:
                    result = await r.json()
            
            if "choices" not in result:
                log(f"[turn {turn}] Relay ERROR: {result.get('error','?')}")
                await ws.send_json({
                    "type": "error",
                    "error": {"message": str(result.get("error", "Unknown error"))}
                })
                continue
            
            content = result["choices"][0].get("message", {}).get("content", "")
            usage = result.get("usage", {})
            log(f"[turn {turn}] Relay OK: '{content[:80]}...' tokens={usage.get('total_tokens','?')}")
            
            # ── Bash code block → ToolCall conversion ──
            bash_pattern = r'```bash\s*\n([\s\S]*?)\n```'
            bash_matches = list(re.finditer(bash_pattern, content))
            tool_calls = []
            
            if bash_matches:
                for m in bash_matches:
                    script = m.group(1).strip()
                    if script:  # skip empty
                        # Extract first line as description
                        lines = script.split('\n')
                        desc = lines[0].strip()[:100] if lines else "run command"
                        tool_calls.append({
                            "call_id": f"call_{uuid.uuid4().hex[:12]}",
                            "name": "exec_command",
                            "arguments": {
                                "cmd": script,
                                "description": desc
                            }
                        })
                # Strip bash blocks from text, keep only brief prefix
                clean_text = re.sub(bash_pattern, '', content).strip()
                if not clean_text:
                    # If all was bash, generate minimal text
                    scripts = [tc["arguments"]["cmd"][:60] for tc in tool_calls]
                    clean_text = "执行命令: " + "; ".join(scripts) if has_chinese else "Running: " + "; ".join(scripts)
                content = clean_text
                log(f"[turn {turn}] Extracted {len(tool_calls)} bash tool call(s)")
            # ── End conversion ──
            
            # Track last assistant message for context continuity
            conversation.append({"role": "assistant", "content": content[:2000]})
            if len(conversation) > 4:
                conversation = conversation[-4:]

            # Event sequence per OpenAI Responses API WebSocket protocol
            events = [
                {"type": "response.created", "response": {
                    "id": resp_id, "object": "response", "status": "in_progress",
                    "model": model_id, "output": []
                }},
                {"type": "response.in_progress", "response": {
                    "id": resp_id, "object": "response", "status": "in_progress",
                    "model": model_id, "output": []
                }},
                {"type": "response.output_item.added", "output_index": 0, "item": {
                    "id": item_id, "object": "realtime.item", "type": "message",
                    "status": "in_progress", "role": "assistant", "content": []
                }},
                {"type": "response.content_part.added", "output_index": 0,
                 "item_id": item_id, "content_index": 0, "part": {
                    "id": part_id, "object": "realtime.part", "type": "text",
                    "status": "in_progress"
                }},
            ]
            
            # Text delta (only if there's text content)
            if content:
                events.append(
                    {"type": "response.output_text.delta", "output_index": 0,
                     "item_id": item_id, "content_index": 0, "delta": content}
                )
            
            events.append(
                {"type": "response.content_part.done", "output_index": 0,
                 "item_id": item_id, "content_index": 0,
                 "part": {"id": part_id, "object": "realtime.part", "type": "text", "status": "completed"}}
            )
            
            # Tool call events (if any)
            if tool_calls:
                tc = tool_calls[0]  # handle first tool call
                tc_id = f"fc_{uuid.uuid4().hex[:12]}"
                tc_args_json = json.dumps(tc["arguments"])
                
                events.append(
                    {"type": "response.output_item.added", "output_index": 1, "item": {
                        "id": tc_id, "object": "realtime.item", "type": "function_call",
                        "status": "in_progress", "call_id": tc["call_id"], "name": "exec_command"
                    }}
                )
                events.append(
                    {"type": "response.function_call_arguments.delta", "output_index": 1,
                     "item_id": tc_id, "delta": tc_args_json}
                )
                events.append(
                    {"type": "response.output_item.done", "output_index": 1, "item": {
                        "id": tc_id, "object": "realtime.item", "type": "function_call",
                        "status": "completed", "call_id": tc["call_id"], "name": "exec_command",
                        "arguments": tc_args_json
                    }}
                )
                log(f"[turn {turn}] Injected tool call: {tc['arguments']['description'][:60]}")
            
            events.append(
                {"type": "response.output_item.done", "output_index": 0, "item": {
                    "id": item_id, "object": "realtime.item", "type": "message",
                    "status": "completed", "role": "assistant",
                    "content": [{"type": "output_text", "text": content, "annotations": []}]
                }}
            )
            events.append(
                {"type": "response.completed", "response": {
                    "id": resp_id, "object": "response", "status": "completed",
                    "model": model_id,
                    "output": [
                        {
                            "id": item_id, "object": "realtime.item", "type": "message",
                            "status": "completed", "role": "assistant",
                            "content": [{"type": "output_text", "text": content, "annotations": []}]
                        }
                    ] + ([{
                        "id": tc_id, "object": "realtime.item", "type": "function_call",
                        "status": "completed", "call_id": tc["call_id"], "name": "exec_command",
                        "arguments": tc_args_json
                    }] if tool_calls else []),
                    "usage": {
                        "input_tokens": usage.get("prompt_tokens", 0),
                        "output_tokens": usage.get("completion_tokens", 0),
                        "total_tokens": usage.get("total_tokens", 0)
                    }
                }}
            )
            
            for event in events:
                await ws.send_json(event)
            log(f"[turn {turn}] Sent {len(events)} events, WS stays open")
            # Do NOT close — let Codex continue the conversation
                
    except Exception as e:
        log(f"WS ERROR: {e}")
        try:
            await ws.send_json({"type": "error", "error": {"message": str(e)}})
        except:
            pass
    log(f"WS connection closed after {turn} turns")
    return ws

async def proxy_handler(request):
    log(f"[HTTP] {request.method} {request.path_qs}")
    async with aiohttp.ClientSession() as session:
        body = await request.read()
        headers = {k: v for k, v in request.headers.items()
                   if k.lower() not in ('host',)}
        url = f"{FLASK_RELAY}{request.path_qs}"
        async with session.request(
            request.method, url, headers=headers, data=body,
            timeout=aiohttp.ClientTimeout(total=120)
        ) as resp:
            response_body = await resp.read()
            return web.Response(
                status=resp.status, body=response_body,
                headers={k: v for k, v in resp.headers.items()
                         if k.lower() != 'transfer-encoding'}
            )

app = web.Application()
app.router.add_get('/v1/responses', ws_handler)
app.router.add_route('*', '/{tail:.*}', proxy_handler)

if __name__ == '__main__':
    log("=== Bridge v2 (persistent WS) starting on :8848 ===")
    web.run_app(app, host='127.0.0.1', port=8848, print=log)
