# app/data_loader.py
# Loads RA Groups synthetic company knowledge from a local JSON file.

import json
from pathlib import Path
from typing import Any, Dict, Optional

DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "ra_groups_knowledge.json"


def load_ra_groups_knowledge() -> Optional[Dict[str, Any]]:
    """
    Loads the synthetic RA Groups knowledge JSON.
    Returns None if file missing or invalid.

    You will later replace the content of ra_groups_knowledge.json
    with your full synthetic dataset.
    """
    if not DATA_PATH.exists():
        return None
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None
