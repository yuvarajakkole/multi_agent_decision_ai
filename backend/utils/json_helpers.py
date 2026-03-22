import json
import re
from typing import Any, Dict


def safe_json_loads(text: str) -> Dict[str, Any]:
    """Parse JSON from LLM output, handling markdown fences and extra text."""
    if not text:
        return {}

    cleaned = text.strip()
    cleaned = re.sub(r"```json", "", cleaned)
    cleaned = re.sub(r"```", "", cleaned)

    try:
        return json.loads(cleaned)
    except Exception:
        pass

    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass

    return {}


def pretty_json(data: Dict[str, Any]) -> str:
    try:
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception:
        return "{}"


def safe_get(data: Dict, key: str, default=None):
    if not isinstance(data, dict):
        return default
    return data.get(key, default)


def normalize_numeric(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default
