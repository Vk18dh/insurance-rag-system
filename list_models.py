import os
import json
import urllib.request
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# 1. List OpenRouter Models
print("--- OpenRouter Models ---")
or_key = os.environ.get("OPENROUTER_API_KEY")
if or_key:
    try:
        url = "https://openrouter.ai/api/v1/models"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {or_key}"})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            # Find any gemini models
            gemini_models = [m["id"] for m in data.get("data", []) if "gemini" in m["id"].lower()]
            print("Available Gemini models on OpenRouter:")
            for m in gemini_models[:10]: # Show first 10
                print(f"  - {m}")
    except Exception as e:
        print(f"Error fetching OpenRouter models: {e}")
else:
    print("OPENROUTER_API_KEY not found.")

# 2. List Google SDK Models
print("\n--- Google SDK Models ---")
google_key = os.environ.get("GOOGLE_API_KEY")
if google_key:
    try:
        genai.configure(api_key=google_key)
        print("Available models on Google SDK:")
        for m in genai.list_models():
            if "generateContent" in m.supported_generation_methods:
                print(f"  - {m.name}")
    except Exception as e:
        print(f"Error fetching Google models: {e}")
else:
    print("GOOGLE_API_KEY not found.")
