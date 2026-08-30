import requests
import json
import os

print("Testing OpenRouter...")
or_key = "sk-or-MOCK_KEY"
try:
    resp = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {or_key}"},
        json={"model": "openai/gpt-4o-mini", "messages": [{"role": "user", "content": "hi"}]}
    )
    print("OpenRouter Status:", resp.status_code)
    print(resp.text)
except Exception as e:
    print(e)

print("\nTesting Groq (Key 1)...")
g_key1 = "gsk_MOCK_KEY_1"
try:
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {g_key1}"},
        json={"model": "llama3-8b-8192", "messages": [{"role": "user", "content": "hi"}]}
    )
    print("Groq 1 Status:", resp.status_code)
    print(resp.text)
except Exception as e:
    print(e)

print("\nTesting Groq (Key 2)...")
g_key2 = "gsk_MOCK_KEY_2"
try:
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {g_key2}"},
        json={"model": "llama3-8b-8192", "messages": [{"role": "user", "content": "hi"}]}
    )
    print("Groq 2 Status:", resp.status_code)
    print(resp.text)
except Exception as e:
    print(e)
