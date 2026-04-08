import os
import json
import urllib.request
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

results = []

# 1. OpenRouter
or_key = os.environ.get("OPENROUTER_API_KEY")
if or_key:
    try:
        url = "https://openrouter.ai/api/v1/models"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {or_key}"})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            gemini_models = [m["id"] for m in data.get("data", []) if "gemini" in m["id"].lower()]
            results.append("OpenRouter Models:")
            results.extend(gemini_models[:20])
    except Exception as e:
        results.append(f"OR Error: {e}")

# 2. Google SDK
google_key = os.environ.get("GOOGLE_API_KEY")
if google_key:
    try:
        genai.configure(api_key=google_key)
        results.append("\nGoogle SDK Models:")
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                results.append(m.name)
    except Exception as e:
        results.append(f"Google Error: {e}")

with open("available_models.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(results))
print("Done")
