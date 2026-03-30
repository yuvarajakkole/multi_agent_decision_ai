"""utils/request_id.py"""
import uuid, time

def new_id() -> str:
    return f"req_{int(time.time())}_{uuid.uuid4().hex[:8]}"
