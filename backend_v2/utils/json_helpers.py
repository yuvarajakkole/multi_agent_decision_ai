import json, re
from typing import Any, Dict

def safe_json_loads(text: str) -> Dict[str, Any]:
    if not text: return {}
    cleaned = re.sub(r"```json|```", "", text.strip()).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    m = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if m:
        try: return json.loads(m.group())
        except Exception: pass
    return {}

def pretty_json(data: Dict) -> str:
    try:    return json.dumps(data, indent=2, ensure_ascii=False)
    except: return "{}"

def safe_get(data: Dict, key: str, default=None):
    return data.get(key, default) if isinstance(data, dict) else default
