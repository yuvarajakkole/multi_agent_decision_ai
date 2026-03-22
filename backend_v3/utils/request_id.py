import uuid,time
def generate_request_id(): return f"req_{int(time.time())}_{uuid.uuid4().hex[:8]}"
