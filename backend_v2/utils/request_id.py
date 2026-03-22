import uuid, time

def generate_request_id() -> str:
    return f"req_{int(time.time())}_{uuid.uuid4().hex[:8]}"
