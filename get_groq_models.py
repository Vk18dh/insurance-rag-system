import os
import json
import urllib.request
from dotenv import load_dotenv

load_dotenv()
api_key = os.environ.get("GROQ_API_KEY")

url = "https://api.groq.com/openai/v1/models"
headers = {
    "Authorization": f"Bearer {api_key}"
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req) as response:
        resp_body = response.read().decode("utf-8")
        models = json.loads(resp_body)
        print("AVAILABLE GROQ MODELS:")
        for m in models.get("data", []):
            print(f"- {m['id']}")
except Exception as e:
    if hasattr(e, 'read'):
        print(f"FAILED: {e.code} - {e.read().decode('utf-8')}")
    else:
        print(f"FAILED: {e}")
