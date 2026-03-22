import uuid
import time
import threading


def generate_request_id() -> str:
    """
    Generate a unique ID for each user request.
    Format: req_<unix_timestamp>_<8-char uuid hex>
    Example: req_1709012398_a1b2c3d4
    """
    timestamp  = int(time.time())
    short_uuid = uuid.uuid4().hex[:8]
    return f"req_{timestamp}_{short_uuid}"


# Thread-local storage for request context (used in logging)
_thread_local = threading.local()


def set_request_id(request_id: str):
    _thread_local.request_id = request_id


def get_request_id() -> str:
    return getattr(_thread_local, "request_id", "unknown")


def generate_agent_execution_id(agent_name: str) -> str:
    """
    Generate a unique ID for a specific agent execution step.
    Example: market_agent_17090123_abcd12
    """
    timestamp  = int(time.time())
    short_uuid = uuid.uuid4().hex[:6]
    return f"{agent_name}_{timestamp}_{short_uuid}"
