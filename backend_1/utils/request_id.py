import uuid
import time
import threading

# ---------------------------------------------------------
# REQUEST ID GENERATION
# ---------------------------------------------------------

def generate_request_id() -> str:
    """
    Generates a unique request id for each user query.

    Format example:
    req_1709012398_a1b2c3d4
    """

    timestamp = int(time.time())
    short_uuid = uuid.uuid4().hex[:8]

    return f"req_{timestamp}_{short_uuid}"


# ---------------------------------------------------------
# THREAD LOCAL CONTEXT
# ---------------------------------------------------------

_thread_local = threading.local()


def set_request_id(request_id: str):
    """
    Store request id in thread-local storage.
    Allows logging across the execution pipeline.
    """
    _thread_local.request_id = request_id


def get_request_id() -> str:
    """
    Retrieve current request id.
    """

    return getattr(_thread_local, "request_id", "unknown_request")


# ---------------------------------------------------------
# AGENT EXECUTION ID
# ---------------------------------------------------------

def generate_agent_execution_id(agent_name: str) -> str:
    """
    Generate unique id for agent execution.

    Example:
    market_agent_17090123_abcd
    """

    timestamp = int(time.time())
    short_uuid = uuid.uuid4().hex[:6]

    return f"{agent_name}_{timestamp}_{short_uuid}"