# Codex Responses API WebSocket Message Format

Codex CLI v0.140.0 uses OpenAI's Responses API over WebSocket. The message
structure is critical for building a working bridge.

## Incoming Message (Codex → Bridge)

```json
{
  "type": "response.create",
  "model": "deepseek-chat",
  "instructions": "<full system prompt + user message, 20K+ chars>",
  "input": [],
  "max_output_tokens": 4096,
  "temperature": 0.7
}
```

### Field Roles

| Field | Turn 1 | Turn 2+ |
|-------|--------|---------|
| `instructions` | Full Codex system prompt + user's message, 20,771 chars | Same as turn 1 |
| `input` | `[]` (empty!) | `[{type: "message", role: "developer", content: [{type: "input_text", text: "..."}]}]` — permissions/env context |
| `model` | User-specified model ID | Same |
| `max_output_tokens` | User config | Same |

### Critical Insight

**The user's actual message is embedded INSIDE `instructions`, not in `input`.**
On turn 1, `input` is an empty array. If the bridge tries to extract the user
message from `input`, it gets nothing → sends a blank user message → the model
only sees the system prompt → responds with "I understand my role..." endlessly.

**Correct approach:** Pass `instructions` in its entirety as a single user
message. The upstream LLM will parse out the user's request from the system
prompt context.

## Outgoing Events (Bridge → Codex)

Bridge must send these events in this exact sequence:

```json
{"type": "session.created", "session": {"id": "...", "model": "deepseek-chat", "modalities": ["text"], "context_window": 128000, "max_output_tokens": 16384}}
{"type": "response.created", "response": {"id": "resp_...", "object": "response", "status": "in_progress", "model": "deepseek-chat", "output": []}}
{"type": "response.in_progress", "response": {"id": "resp_...", "object": "response", "status": "in_progress", "model": "deepseek-chat", "output": []}}
{"type": "response.output_item.added", "output_index": 0, "item": {"id": "item_...", "object": "realtime.item", "type": "message", "status": "in_progress", "role": "assistant", "content": []}}
{"type": "response.content_part.added", "output_index": 0, "item_id": "item_...", "content_index": 0, "part": {"id": "part_...", "object": "realtime.part", "type": "text", "status": "in_progress"}}
{"type": "response.output_text.delta", "output_index": 0, "item_id": "item_...", "content_index": 0, "delta": "<full response text>"}
{"type": "response.content_part.done", "output_index": 0, "item_id": "item_...", "content_index": 0, "part": {"id": "part_...", "object": "realtime.part", "type": "text", "status": "completed"}}
{"type": "response.output_item.done", "output_index": 0, "item": {"id": "item_...", "object": "realtime.item", "type": "message", "status": "completed", "role": "assistant", "content": [{"type": "output_text", "text": "<full response>", "annotations": []}]}}
{"type": "response.completed", "response": {"id": "resp_...", "object": "response", "status": "completed", "model": "deepseek-chat", "output": [...], "usage": {...}}}
```

### Key Points

- `session.created` must be sent immediately after WebSocket handshake (before any messages). Codex's `codex doctor` checks for `server model present` — this event provides it.
- All IDs must be unique per response (`uuid4().hex[:24]` format works).
- `response.output_text.delta` carries the FULL text (not incremental — we use non-streaming upstream).
- The WS must stay open after events are sent — Codex will send more `response.create` messages for follow-up turns.
- Closing is Codex's responsibility. The bridge should only close on error or when Codex initiates close.

## Conversation Continuity

Codex sends the same 20K+ `instructions` in every turn. The bridge should:

1. Pass each turn's `instructions` as a fresh user message
2. Accumulate assistant responses in a conversation list (last 2-4 messages)
3. Prepend the recent conversation history to provide context for multi-turn interactions
4. Inject a language hint when Chinese characters are detected: `"Respond in Chinese (Simplified)."` as a system message

## Debugging

- Bridge logs to `/tmp/codex_bridge.log`
- `codex doctor` is the most valuable debug tool — shows base URL, WS endpoint, handshake result, route probes
- HTTP 101 on handshake = bridge accepted the WS connection
- HTTP 401 on route probe = `CODEX_API_KEY` doesn't match relay's `local_token`
- Empty response / timeout = likely `instructions`/`input` confusion
