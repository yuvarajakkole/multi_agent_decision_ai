from langgraph.checkpoint.memory import MemorySaver
from typing import Dict
import threading


# ---------------------------------------------------------
# GLOBAL MEMORY SAVER
# ---------------------------------------------------------

_memory_saver = MemorySaver()


def get_memory_saver():
    """
    Returns global MemorySaver instance.
    Used by LangGraph when compiling graphs.
    """
    return _memory_saver


# ---------------------------------------------------------
# SESSION MEMORY REGISTRY
# ---------------------------------------------------------

_session_registry: Dict[str, Dict] = {}

_lock = threading.Lock()


def create_session_memory(session_id: str):
    """
    Initialize memory storage for a session.
    """

    with _lock:

        if session_id not in _session_registry:

            _session_registry[session_id] = {
                "execution_count": 0,
                "agent_history": []
            }


def get_session_memory(session_id: str) -> Dict:
    """
    Retrieve memory for a session.
    """

    with _lock:

        return _session_registry.get(session_id, {})


def update_session_execution(session_id: str, agent_name: str):
    """
    Track agent executions.
    """

    with _lock:

        session = _session_registry.get(session_id)

        if not session:
            return

        session["execution_count"] += 1

        session["agent_history"].append(agent_name)


def reset_session(session_id: str):
    """
    Reset memory for a session.
    """

    with _lock:

        if session_id in _session_registry:
            del _session_registry[session_id]