import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GROQ_API_KEY")

models_to_test = [
    "llama3-8b-8192",
    "llama-3.1-8b-instant",
    "llama-3.3-70b-versatile",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
    "groq/compound"
]

url = "https://api.groq.com/openai/v1/chat/completions"

for model in models_to_test:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    data = {
        "model": model,
        "messages": [
            {"role": "user", "content": "Hello"}
        ]
    }
    
    req = urllib.request.Request(url, data=json.dumps(data).encode("utf-8"), headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as response:
            resp_body = response.read().decode("utf-8")
            print(f"SUCCESS: {model}")
    except Exception as e:
        if hasattr(e, 'read'):
            print(f"FAILED: {model} - {e.code} - {e.read().decode('utf-8')}")
        else:
            print(f"FAILED: {model} - {e}")
