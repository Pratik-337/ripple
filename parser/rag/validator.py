import requests
import json
import re
import hashlib
import os

OLLAMA_URL = 'http://localhost:11434/api/generate'
MODEL = 'qwen2:0.5b'
CACHE_FILE = 'impact_cache.json'

def get_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f: return json.load(f)
        except: return {}
    return {}

def save_cache(cache):
    with open(CACHE_FILE, 'w') as f: json.dump(cache, f)

def validate_impact(changed_code: str, candidate_code: str, change_type: str = 'LOGIC_CHANGE'):
    # Pillar: Decision Caching
    pair_id = hashlib.md5((changed_code + candidate_code + change_type).encode()).hexdigest()
    cache = get_cache()
    if pair_id in cache: return cache[pair_id]

    prompt = f'''[STRICT ANALYSIS]
Change: {changed_code}
Target: {candidate_code}

Task: If Code A has a {change_type}, does Code B require review? Respond ONLY in JSON: {{"impact": true/false, "reason": "str"}}'''

    try:
        # Pillar: Strict Determinism
        response = requests.post(
            OLLAMA_URL,
            json={
                'model': MODEL,
                'prompt': prompt,
                'stream': False,
                'options': {'temperature': 0, 'seed': 42, 'num_predict': 64}
            },
            timeout=30
        )
        result = response.json()
        if 'response' in result:
            match = re.search(r'\{.*\}', result['response'], re.DOTALL)
            if match:
                data = json.loads(match.group())
                decision = {
                    'is_impacted': bool(data.get('impact', False)),
                    'reason': str(data.get('reason', 'Semantic link')),
                    'suggested_fix': None,
                    'confidence': 0.8
                }
                cache[pair_id] = decision
                save_cache(cache)
                return decision
    except:
        pass
    return {'is_impacted': False, 'reason': 'Structural only (fallback)', 'suggested_fix': None, 'confidence': 0.0}
