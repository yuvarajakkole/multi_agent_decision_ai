import json,re
def safe_json_loads(text):
    if not text: return {}
    try: return json.loads(re.sub(r"```json|```","",text.strip()).strip())
    except: pass
    m=re.search(r"\{.*\}",text,re.DOTALL)
    if m:
        try: return json.loads(m.group())
        except: pass
    return {}
