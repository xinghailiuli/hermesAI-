import os, json, time, threading, requests
from flask import Flask, request, jsonify, send_from_directory

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
    return token == CONFIG['auth']['local_token']

@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'models': len(CONFIG['models'])})

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
            models.append({'id': m['id'], 'object': 'model', 'owned_by': m['provider']})
    return jsonify({'object': 'list', 'data': models})

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
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
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

@app.route('/')
def dashboard():
    return send_from_directory('.', 'dashboard.html')

if __name__ == '__main__':
    host = CONFIG['server'].get('host', '127.0.0.1')
    port = CONFIG['server'].get('port', 8848)
    debug = CONFIG['server'].get('debug', False)
    app.run(host=host, port=port, debug=debug)
