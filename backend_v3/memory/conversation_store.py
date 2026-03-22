import threading; _store={}; _lock=threading.Lock()
def add_message(sid,role,content):
    with _lock: _store.setdefault(sid,[]).append({"role":role,"content":content})
def get_history(sid):
    with _lock: return _store.get(sid,[])
