import httpx
import json
import re

async def analyze_with_llm(diff_content: str, context_files: list[str]) -> list[dict]:
    prompt = f"""
You are analyzing a code change. Here is the diff:
{diff_content}

Here are the files that may be affected:
{context_files}

For each affected location, respond with JSON only:
[
  {{"file": "path", "line": 1, "reason": "str", "suggested_fix": "str", "confidence": 0.9}}
]
    """
    
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "deepseek-coder:6.7b",
        "prompt": prompt,
        "stream": False
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            
            data = resp.json()
            response_text = data.get("response", "")
            
            # Simple heuristic to extract JSON array
            match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if match:
                json_str = match.group(0)
                return json.loads(json_str)
            else:
                return []
    except Exception as e:
        print(f"LLM Impact Analysis failed: {e}")
        return []
