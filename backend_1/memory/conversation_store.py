import threading
from typing import Dict, List


# ---------------------------------------------------------
# GLOBAL CONVERSATION STORE
# ---------------------------------------------------------

_conversations: Dict[str, List[Dict]] = {}

_lock = threading.Lock()


# ---------------------------------------------------------
# ADD MESSAGE
# ---------------------------------------------------------

def add_message(session_id: str, role: str, content: str):
    """
    Add a message to the conversation history.
    """

    with _lock:

        if session_id not in _conversations:
            _conversations[session_id] = []

        _conversations[session_id].append({
            "role": role,
            "content": content
        })


# ---------------------------------------------------------
# GET HISTORY
# ---------------------------------------------------------

def get_history(session_id: str) -> List[Dict]:
    """
    Retrieve full conversation history.
    """

    with _lock:

        return _conversations.get(session_id, [])


# ---------------------------------------------------------
# CLEAR HISTORY
# ---------------------------------------------------------

def clear_history(session_id: str):
    """
    Delete conversation history.
    """

    with _lock:

        if session_id in _conversations:
            del _conversations[session_id]


# ---------------------------------------------------------
# LAST USER QUERY
# ---------------------------------------------------------

def get_last_user_query(session_id: str):

    history = get_history(session_id)

    for msg in reversed(history):

        if msg["role"] == "user":
            return msg["content"]

    return None