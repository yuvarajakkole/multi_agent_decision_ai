import json
import re
from typing import Any, Dict


# ---------------------------------------------------------
# SAFE JSON PARSER
# ---------------------------------------------------------

def safe_json_loads(text: str) -> Dict[str, Any]:
    """
    Safely parse JSON from LLM outputs.

    Handles cases like:
    - ```json blocks
    - extra text
    - invalid formatting
    """

    if not text:
        return {}

    # Remove markdown json blocks
    cleaned = text.strip()

    cleaned = re.sub(r"```json", "", cleaned)
    cleaned = re.sub(r"```", "", cleaned)

    # Try normal parsing
    try:
        return json.loads(cleaned)

    except Exception:
        pass

    # Try extracting JSON substring
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)

    if match:
        try:
            return json.loads(match.group())
        except Exception:
            return {}

    return {}


# ---------------------------------------------------------
# JSON PRETTY PRINT
# ---------------------------------------------------------

def pretty_json(data: Dict[str, Any]) -> str:
    """
    Convert dict → formatted JSON string.
    """

    try:
        return json.dumps(data, indent=2, ensure_ascii=False)
    except Exception:
        return "{}"


# ---------------------------------------------------------
# SAFE GET
# ---------------------------------------------------------

def safe_get(data: Dict, key: str, default=None):
    """
    Safe dictionary getter.
    """

    if not isinstance(data, dict):
        return default

    return data.get(key, default)


# ---------------------------------------------------------
# VALIDATE REQUIRED KEYS
# ---------------------------------------------------------

def validate_required_keys(data: Dict, required_keys):
    """
    Validate if required keys exist.

    Returns:
        bool
    """

    if not isinstance(data, dict):
        return False

    for key in required_keys:
        if key not in data:
            return False

    return True


# ---------------------------------------------------------
# NORMALIZE NUMERIC VALUES
# ---------------------------------------------------------

def normalize_numeric(value: Any, default: float = 0.0) -> float:
    """
    Convert numeric values safely.
    """

    try:
        return float(value)
    except Exception:
        return default


# ---------------------------------------------------------
# CLEAN LLM TEXT
# ---------------------------------------------------------

def clean_llm_text(text: str) -> str:
    """
    Remove unnecessary formatting from LLM outputs.
    """

    if not text:
        return ""

    text = text.strip()

    # Remove markdown code blocks
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)

    return text.strip()