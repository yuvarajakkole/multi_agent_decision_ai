from typing import Dict, List
import threading

_store: Dict[str, List[Dict]] = {}
_lock = threading.Lock()


def save_conversation(request_id: str, user_query: str, final_report: str, decision: str):
    """Persist a completed conversation for history retrieval."""
    with _lock:
        if request_id not in _store:
            _store[request_id] = []
        _store[request_id].append({
            "user_query":   user_query,
            "decision":     decision,
            "final_report": final_report,
        })


def get_conversation(request_id: str) -> List[Dict]:
    with _lock:
        return _store.get(request_id, [])


def list_all_requests() -> List[str]:
    with _lock:
        return list(_store.keys())
