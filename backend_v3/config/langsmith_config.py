import os
from config.settings import LANGSMITH_API_KEY,LANGSMITH_PROJECT,LANGSMITH_ENDPOINT
if LANGSMITH_API_KEY:
    os.environ["LANGCHAIN_TRACING_V2"]="true"
    os.environ["LANGCHAIN_API_KEY"]=LANGSMITH_API_KEY
    os.environ["LANGCHAIN_PROJECT"]=LANGSMITH_PROJECT
    os.environ["LANGCHAIN_ENDPOINT"]=LANGSMITH_ENDPOINT
def get_langsmith_client():
    if not LANGSMITH_API_KEY: return None
    try:
        from langsmith import Client
        return Client(api_key=LANGSMITH_API_KEY,api_url=LANGSMITH_ENDPOINT)
    except: return None
