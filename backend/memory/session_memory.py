from langgraph.checkpoint.memory import MemorySaver
from typing import Dict
import threading

_memory_saver = MemorySaver()


def get_memory_saver() -> MemorySaver:
    """Returns the global MemorySaver for LangGraph checkpoint support."""
    return _memory_saver


_session_registry: Dict[str, Dict] = {}
_lock = threading.Lock()


def create_session(session_id: str):
    with _lock:
        if session_id not in _session_registry:
            _session_registry[session_id] = {
                "execution_count": 0,
                "agent_history": []
            }


def get_session(session_id: str) -> Dict:
    with _lock:
        return _session_registry.get(session_id, {})


def update_session(session_id: str, agent_name: str):
    with _lock:
        session = _session_registry.get(session_id)
        if session:
            session["execution_count"] += 1
            session["agent_history"].append(agent_name)


def reset_session(session_id: str):
    with _lock:
        _session_registry.pop(session_id, None)
