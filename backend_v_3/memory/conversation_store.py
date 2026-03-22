import threading
from typing import Dict, List

_store: Dict[str, List[Dict]] = {}
_lock = threading.Lock()

def add_message(session_id: str, role: str, content: str):
    with _lock:
        _store.setdefault(session_id, []).append({"role": role, "content": content})

def get_history(session_id: str) -> List[Dict]:
    with _lock: return _store.get(session_id, [])

def clear_history(session_id: str):
    with _lock: _store.pop(session_id, None)
