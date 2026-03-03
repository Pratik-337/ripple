import requests
import json
import re
import hashlib
import os
import time

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2:0.5b"
CACHE_FILE = "impact_cache.json"
LOG_FILE = "impact_audit.jsonl"

def get_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f: return json.load(f)
        except: return {}
    return {}

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)

def audit_log(data):
    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps({**data, "timestamp": time.ctime()}) + "\n")
    except:
        pass

def validate_impact(changed_code, candidate_code, change_type="LOGIC_CHANGE", relationship="SEMANTIC"):
    pair_id = hashlib.md5((changed_code + candidate_code + str(change_type) + str(relationship)).encode()).hexdigest()
    cache = get_cache()
    if pair_id in cache: return cache[pair_id]

    prompt = f"[ROLE] Architect\n[CONTEXT] Change: {change_type} | Link: Target {relationship} Change\n[CODE A (Changed)]\n{changed_code}\n[CODE B (Target)]\n{candidate_code}\n[TASK] Based on the {relationship} link, does changing A impact B?\n[SCHEMA]\n{{\"impact\": boolean, \"reason\": \"string\", \"confidence\": float}}"

    try:
        response = requests.post(OLLAMA_URL, json={
            "model": MODEL, 
            "prompt": prompt, 
            "stream": False,
            "options": {"temperature": 0, "seed": 42, "num_predict": 128}
        }, timeout=45)
        res = response.json()
        
        txt = res.get("response", "")
        m = re.search(r"\{.*\}", txt, re.DOTALL)
        if m:
            d = json.loads(m.group())
            is_imp = bool(d.get("impact", False))
            reason = str(d.get("reason", "Semantic link")).strip()
            
            negations = ["no impact", "not affect", "no direct", "independent", "no change", "not require"]
            if is_imp and any(n in reason.lower() for n in negations):
                is_imp = False
                reason = f"[Auto-Reject] Contradiction: {reason}"

            decision = {
                "is_impacted": is_imp, 
                "reason": f"[{relationship}] {reason}", 
                "suggested_fix": d.get("suggested_fix"), 
                "confidence": float(d.get("confidence", 0.8))
            }
            audit_log({"pair_id": pair_id, "change_type": change_type, "decision": decision})
            cache[pair_id] = decision
            save_cache(cache)
            return decision
    except Exception as e:
        audit_log({"pair_id": pair_id, "error": str(e)})

    return {"is_impacted": False, "reason": f"[{relationship}] Structural only", "suggested_fix": None, "confidence": 0.0}
