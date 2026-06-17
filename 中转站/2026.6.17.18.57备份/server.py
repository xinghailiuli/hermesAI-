import os, json, time, threading, requests, uuid
from flask import Flask, request, jsonify, send_from_directory, Response, stream_with_context

app = Flask(__name__, static_folder='.', static_url_path='')

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json')
with open(CONFIG_PATH) as f:
    CONFIG = json.load(f)

DASHSCOPE_BASE = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
DASHSCOPE_KEY = os.getenv('DASHSCOPE_API_KEY', '')
DEEPSEEK_KEY = os.getenv('DEEPSEEK_API_KEY', '')
SILICONFLOW_KEY = os.getenv('SILICONFLOW_API_KEY', '')
SENSENOVA_KEY = os.getenv('SENSENOVA_API_KEY', '')

stats = {'total_requests': 0, 'total_tokens': 0, 'last_request': None}
stats_lock = threading.Lock()

def get_upstream_key(provider):
    env_map = {
        'deepseek': DEEPSEEK_KEY,
        'siliconflow': SILICONFLOW_KEY,
        'dashscope': DASHSCOPE_KEY,
        'sensenova': SENSENOVA_KEY,
    }
    return env_map.get(provider, '')

def get_model_config(model_id):
    for m in CONFIG['models']:
        if m['id'] == model_id and m.get('enabled', True):
            return m
    if DASHSCOPE_KEY:
        return {
            'id': model_id, 'provider': 'dashscope',
            'base_url': DASHSCOPE_BASE, 'model': model_id,
            'enabled': True, '_passthrough': True
        }
    return None

def check_auth():
    if not CONFIG['auth'].get('require_auth', True):
        return True
    auth = request.headers.get('Authorization', '')
    token = auth.replace('Bearer ', '')
    if token == CONFIG['auth']['local_token']:
        return True
    # Also support x-api-key header
    x_api_key = request.headers.get('x-api-key', '')
    if x_api_key == CONFIG['auth']['local_token']:
        return True
    return False

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'models': len(CONFIG['models'])})

@app.route('/')
@app.route('/v1')
@app.route('/v1/')
def api_root():
    return jsonify({
        'object': 'list',
        'data': [],
        'message': 'API relay running'
    })

@app.route('/stats')
def get_stats():
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    with stats_lock:
        return jsonify(stats)

@app.route('/v1/models')
def list_models():
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    models = []
    for m in CONFIG['models']:
        if m.get('enabled', True):
            models.append({
                'id': m['id'],
                'object': 'model',
                'created': 1765900800,
                'owned_by': m['provider'],
                'context_window': 128000,
                'max_output_tokens': 16384,
                'supports_structured_output': True,
                'supports_streaming': True,
                'supports_tool_calling': True,
            })
    return jsonify({'object': 'list', 'data': models}), 200, {'ETag': f'models-{len(models)}'}

@app.route('/v1/models/<model_id>')
def get_model(model_id):
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    for m in CONFIG['models']:
        if m['id'] == model_id and m.get('enabled', True):
            return jsonify({
                'id': m['id'],
                'object': 'model',
                'created': 1765900800,
                'owned_by': m['provider'],
                'context_window': 128000,
                'max_output_tokens': 16384,
            })
    return jsonify({'error': f'Model {model_id} not found'}), 404

@app.route('/v1/models/dashscope')
def list_dashscope_models():
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    if not DASHSCOPE_KEY:
        return jsonify({'error': 'DASHSCOPE_API_KEY not set'}), 500
    try:
        r = requests.get(f'{DASHSCOPE_BASE}/models',
            headers={'Authorization': f'Bearer {DASHSCOPE_KEY}'}, timeout=15)
        all_models = r.json().get('data', [])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    exclude = ['tts', 'asr', 'speech', 'realtime', 'image', 'wan',
               'livetranslate', 'mt-', 'ocr', 'omni', 'gui', 'audio',
               'vc-', 'vd-', 's2s', 'xiaomi', 'vanchin']

    def cat(mid):
        if any(x in mid for x in ['qwen3.7', 'qwen3.6']): return '最新旗舰'
        if 'qwen3.5' in mid: return 'Qwen3.5'
        if any(x in mid for x in ['qwq', 'qvq', 'deep-research']): return '深度推理'
        if 'coder' in mid: return '代码编程'
        if 'math' in mid: return '数学推理'
        if 'qwen3' in mid: return 'Qwen3'
        if 'deepseek' in mid: return 'DeepSeek'
        if 'kimi' in mid: return 'Kimi'
        if 'glm' in mid: return '智谱GLM'
        if 'minimax' in mid: return 'MiniMax'
        if any(x in mid for x in ['qwen-', 'qwen1', 'qwen2']): return '经典系列'
        return '其他'

    filtered = []
    for m in all_models:
        mid = m.get('id', '')
        if any(x in mid.lower() for x in exclude):
            continue
        filtered.append({'id': mid, '_cat': cat(mid.lower())})

    return jsonify({'object': 'list', 'data': filtered})

@app.route('/v1/chat/completions', methods=['POST'])
def chat_completions():
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400

    model_id = data.get('model', '')
    cfg = get_model_config(model_id)
    if not cfg:
        return jsonify({'error': f'Model {model_id} not found'}), 404

    provider = cfg['provider']
    api_key = get_upstream_key(provider)
    if not api_key:
        return jsonify({'error': f'API key not configured for {provider}'}), 500

    upstream_model = cfg['model']
    if upstream_model == '_passthrough':
        upstream_model = model_id

    url = f"{cfg['base_url']}/chat/completions"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    payload = {
        'model': upstream_model,
        'messages': data.get('messages', []),
        'max_tokens': data.get('max_tokens', 4096),
        'temperature': data.get('temperature', 0.7),
        'stream': False
    }
    if 'top_p' in data:
        payload['top_p'] = data['top_p']

    if provider == 'sensenova' and 'deepseek' in upstream_model:
        payload['thinking'] = {'type': 'disabled'}

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=120)
        result = r.json()

        if provider == 'sensenova':
            for choice in result.get('choices', []):
                msg = choice.get('message', {})
                if not msg.get('content') and msg.get('reasoning'):
                    msg['content'] = msg.pop('reasoning')

        with stats_lock:
            stats['total_requests'] += 1
            stats['total_tokens'] += result.get('usage', {}).get('total_tokens', 0)
            stats['last_request'] = time.strftime('%Y-%m-%d %H:%M:%S')

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 502

# ── Anthropic Messages API ──

def anthropic_to_openai(anthropic_data):
    """Convert Anthropic Messages request to OpenAI Chat Completions format."""
    messages = []
    system_prompt = anthropic_data.get('system', '')
    
    if system_prompt:
        if isinstance(system_prompt, list):
            for s in system_prompt:
                if isinstance(s, dict) and s.get('type') == 'text':
                    messages.append({'role': 'system', 'content': s['text']})
                elif isinstance(s, str):
                    messages.append({'role': 'system', 'content': s})
        else:
            messages.append({'role': 'system', 'content': system_prompt})
    
    for msg in anthropic_data.get('messages', []):
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        if isinstance(content, list):
            text_parts = [c.get('text', '') for c in content if c.get('type') == 'text']
            content = '\n'.join(text_parts) if text_parts else ''
        messages.append({'role': role, 'content': content})
    
    return {
        'model': anthropic_data.get('model', 'deepseek-chat'),
        'messages': messages,
        'max_tokens': anthropic_data.get('max_tokens', 4096),
        'temperature': anthropic_data.get('temperature', 0.7),
        'stream': anthropic_data.get('stream', False),
    }

def openai_to_anthropic(openai_resp, model_id, req_id=None):
    """Convert OpenAI response to Anthropic Messages format."""
    if not req_id:
        req_id = f"msg_{uuid.uuid4().hex[:24]}"
    choice = openai_resp.get('choices', [{}])[0]
    content = choice.get('message', {}).get('content', '')
    usage = openai_resp.get('usage', {})
    
    return {
        'id': req_id,
        'type': 'message',
        'role': 'assistant',
        'content': [{'type': 'text', 'text': content}],
        'model': model_id,
        'stop_reason': choice.get('finish_reason', 'end_turn'),
        'stop_sequence': None,
        'usage': {
            'input_tokens': usage.get('prompt_tokens', 0),
            'output_tokens': usage.get('completion_tokens', 0),
        }
    }

@app.route('/v1/messages', methods=['POST'])
def anthropic_messages():
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    
    model_id = data.get('model', 'deepseek-chat')
    # Map any Claude/Anthropic model names to deepseek-chat
    if 'claude' in model_id.lower() or 'anthropic' in model_id.lower():
        model_id = 'deepseek-chat'
    cfg = get_model_config(model_id)
    if not cfg:
        cfg = get_model_config('deepseek-chat')  # fallback
    if not cfg:
        return jsonify({'error': f'Model {model_id} not found'}), 404
    
    provider = cfg['provider']
    api_key = get_upstream_key(provider)
    if not api_key:
        return jsonify({'error': f'API key not configured for {provider}'}), 500
    
    upstream_model = cfg['model']
    if upstream_model == '_passthrough':
        upstream_model = model_id
    
    oai_payload = anthropic_to_openai(data)
    oai_payload['model'] = upstream_model
    
    url = f"{cfg['base_url']}/chat/completions"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    if provider == 'sensenova' and 'deepseek' in upstream_model:
        oai_payload['thinking'] = {'type': 'disabled'}
    
    is_stream = data.get('stream', False)
    req_id = f"msg_{uuid.uuid4().hex[:24]}"
    
    if is_stream:
        return anthropic_stream_response(url, headers, oai_payload, model_id, req_id)
    
    try:
        r = requests.post(url, headers=headers, json=oai_payload, timeout=120)
        result = r.json()
        
        with stats_lock:
            stats['total_requests'] += 1
            stats['total_tokens'] += result.get('usage', {}).get('total_tokens', 0)
            stats['last_request'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify(openai_to_anthropic(result, model_id, req_id))
    except Exception as e:
        return jsonify({'error': str(e)}), 502


def anthropic_stream_response(url, headers, oai_payload, model_id, req_id):
    """Stream OpenAI SSE → Anthropic SSE."""
    oai_payload['stream'] = True
    
    def generate():
        try:
            r = requests.post(url, headers=headers, json=oai_payload, stream=True, timeout=120)
            
            # event: message_start
            yield f"event: message_start\ndata: {json.dumps({'type': 'message_start', 'message': {'id': req_id, 'type': 'message', 'role': 'assistant', 'content': [], 'model': model_id, 'usage': {'input_tokens': 0, 'output_tokens': 0}}})}\n\n"
            
            # event: content_block_start
            yield f"event: content_block_start\ndata: {json.dumps({'type': 'content_block_start', 'index': 0, 'content_block': {'type': 'text', 'text': ''}})}\n\n"
            
            # event: ping (Anthropic requires periodic pings)
            yield f"event: ping\ndata: {json.dumps({'type': 'ping'})}\n\n"
            
            text_content = ''
            input_tokens = 0
            output_tokens = 0
            
            for line in r.iter_lines(decode_unicode=True):
                if not line or not line.startswith('data: '):
                    continue
                data_str = line[6:]
                if data_str == '[DONE]':
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get('choices', [{}])[0].get('delta', {})
                    content = delta.get('content', '')
                    if content:
                        text_content += content
                        yield f"event: content_block_delta\ndata: {json.dumps({'type': 'content_block_delta', 'index': 0, 'delta': {'type': 'text_delta', 'text': content}})}\n\n"
                    
                    if chunk.get('usage'):
                        input_tokens = chunk['usage'].get('prompt_tokens', 0)
                        output_tokens = chunk['usage'].get('completion_tokens', 0)
                except json.JSONDecodeError:
                    pass
            
            # event: content_block_stop
            yield f"event: content_block_stop\ndata: {json.dumps({'type': 'content_block_stop', 'index': 0})}\n\n"
            
            # event: message_delta
            yield f"event: message_delta\ndata: {json.dumps({'type': 'message_delta', 'delta': {'stop_reason': 'end_turn'}, 'usage': {'output_tokens': output_tokens}})}\n\n"
            
            # event: message_stop
            yield f"event: message_stop\ndata: {json.dumps({'type': 'message_stop'})}\n\n"
            
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'type': 'error', 'error': {'message': str(e)}})}\n\n"
    
    return Response(
        stream_with_context(generate()),
        content_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }
    )

# ── End Anthropic ──

# ── Codex Responses API (OpenAI) ──

def codex_responses_to_openai(codex_data):
    """Convert Codex Responses API request to OpenAI Chat Completions format."""
    messages = []
    instructions = codex_data.get('instructions', '')
    if instructions:
        messages.append({'role': 'system', 'content': instructions})
    
    inp = codex_data.get('input', '')
    if isinstance(inp, list):
        for item in inp:
            if isinstance(item, dict):
                role = item.get('role', 'user')
                content = item.get('content', '')
                if isinstance(content, list):
                    text_parts = [c.get('text', '') for c in content if c.get('type') == 'text']
                    content = '\n'.join(text_parts) if text_parts else ''
                messages.append({'role': role, 'content': content})
            elif isinstance(item, str):
                messages.append({'role': 'user', 'content': item})
    elif isinstance(inp, str) and inp:
        messages.append({'role': 'user', 'content': inp})
    
    if not messages:
        messages.append({'role': 'user', 'content': 'Hello'})
    
    return {
        'model': codex_data.get('model', 'deepseek-chat'),
        'messages': messages,
        'max_tokens': codex_data.get('max_output_tokens', 4096),
        'temperature': codex_data.get('temperature', 0.7),
        'stream': codex_data.get('stream', False),
    }

def openai_to_codex_responses(openai_resp, model_id, req_id=None):
    """Convert OpenAI Chat response to Codex Responses API format."""
    if not req_id:
        req_id = f"resp_{uuid.uuid4().hex[:24]}"
    choice = openai_resp.get('choices', [{}])[0]
    content = choice.get('message', {}).get('content', '')
    usage = openai_resp.get('usage', {})
    
    return {
        'id': req_id,
        'object': 'response',
        'model': model_id,
        'output': [{'type': 'message', 'role': 'assistant', 'content': [{'type': 'output_text', 'text': content}]}],
        'usage': {
            'input_tokens': usage.get('prompt_tokens', 0),
            'output_tokens': usage.get('completion_tokens', 0),
            'total_tokens': usage.get('total_tokens', 0),
        }
    }

@app.route('/v1/responses', methods=['POST', 'GET', 'OPTIONS'])
def codex_responses():
    # Reject WebSocket upgrade cleanly BEFORE parsing body → Codex falls back to HTTPS
    if request.headers.get('Upgrade', '').lower() == 'websocket':
        return jsonify({'error': 'WebSocket not supported, use HTTP'}), 426
    
    if request.method in ('GET', 'OPTIONS'):
        return jsonify({'object': 'list', 'data': []})
    
    if not check_auth():
        return jsonify({'error': 'Unauthorized'}), 401
    
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({'error': 'Invalid JSON'}), 400
    
    model_id = data.get('model', 'deepseek-chat')
    cfg = get_model_config(model_id)
    if not cfg:
        cfg = get_model_config('deepseek-chat')
    if not cfg:
        return jsonify({'error': f'Model {model_id} not found'}), 404
    
    provider = cfg['provider']
    api_key = get_upstream_key(provider)
    if not api_key:
        return jsonify({'error': f'API key not configured for {provider}'}), 500
    
    upstream_model = cfg['model']
    if upstream_model == '_passthrough':
        upstream_model = model_id
    
    oai_payload = codex_responses_to_openai(data)
    oai_payload['model'] = upstream_model
    
    url = f"{cfg['base_url']}/chat/completions"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    if provider == 'sensenova' and 'deepseek' in upstream_model:
        oai_payload['thinking'] = {'type': 'disabled'}
    
    is_stream = data.get('stream', False)
    req_id = f"resp_{uuid.uuid4().hex[:24]}"
    
    if is_stream:
        return codex_stream_response(url, headers, oai_payload, model_id, req_id)
    
    try:
        r = requests.post(url, headers=headers, json=oai_payload, timeout=180)
        result = r.json()
        
        with stats_lock:
            stats['total_requests'] += 1
            stats['total_tokens'] += result.get('usage', {}).get('total_tokens', 0)
            stats['last_request'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        return jsonify(openai_to_codex_responses(result, model_id, req_id))
    except Exception as e:
        return jsonify({'error': str(e)}), 502


def codex_stream_response(url, headers, oai_payload, model_id, req_id):
    """Stream OpenAI SSE → Codex Responses API SSE format."""
    oai_payload['stream'] = True
    
    def generate():
        try:
            r = requests.post(url, headers=headers, json=oai_payload, stream=True, timeout=180)
            
            # response.created event
            yield f"event: response.created\ndata: {json.dumps({'type': 'response.created', 'response': {'id': req_id, 'object': 'response', 'model': model_id, 'output': []}})}\\n\\n"
            
            text_content = ''
            input_tokens = 0
            output_tokens = 0
            
            for line in r.iter_lines(decode_unicode=True):
                if not line or not line.startswith('data: '):
                    continue
                data_str = line[6:]
                if data_str == '[DONE]':
                    break
                try:
                    chunk = json.loads(data_str)
                    delta = chunk.get('choices', [{}])[0].get('delta', {})
                    content = delta.get('content', '')
                    if content:
                        text_content += content
                        yield f"event: response.output_text.delta\ndata: {json.dumps({'type': 'response.output_text.delta', 'delta': content})}\\n\\n"
                    
                    if chunk.get('usage'):
                        input_tokens = chunk['usage'].get('prompt_tokens', 0)
                        output_tokens = chunk['usage'].get('completion_tokens', 0)
                except json.JSONDecodeError:
                    pass
            
            # response.completed event
            yield f"event: response.completed\ndata: {json.dumps({'type': 'response.completed', 'response': {'id': req_id, 'object': 'response', 'model': model_id, 'output': [{'type': 'message', 'role': 'assistant', 'content': [{'type': 'output_text', 'text': text_content}]}], 'usage': {'input_tokens': input_tokens, 'output_tokens': output_tokens, 'total_tokens': input_tokens + output_tokens}}})}\\n\\n"
            
        except Exception as e:
            yield f"event: error\ndata: {json.dumps({'type': 'error', 'error': {'message': str(e)}})}\\n\\n"
    
    return Response(
        stream_with_context(generate()),
        content_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
        }
    )

# ── End Codex ──

@app.route('/')
def dashboard():
    return send_from_directory('.', 'dashboard.html')

if __name__ == '__main__':
    # WebSocket rejection middleware (before app.run)
    _original_wsgi_app = app.wsgi_app
    def _reject_websocket(environ, start_response):
        if environ.get('HTTP_UPGRADE', '').lower() == 'websocket':
            start_response('426 Upgrade Required', [('Content-Type', 'application/json')])
            return [b'{"error":"WebSocket not supported, use HTTP"}']
        return _original_wsgi_app(environ, start_response)
    app.wsgi_app = _reject_websocket
    
    host = CONFIG['server'].get('host', '127.0.0.1')
    port = CONFIG['server'].get('port', 8848)
    debug = CONFIG['server'].get('debug', False)
    app.run(host=host, port=port, debug=debug)
