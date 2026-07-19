import requests
import json

payload = {
    "query": "What are the maturity benefits and conditions under the LIC Bima Jyoti policy?",
    "session_id": "test_123"
}
try:
    resp = requests.post("http://localhost:8000/api/v1/query", json=payload)
    print("Status:", resp.status_code)
    print("Response JSON:")
    print(json.dumps(resp.json(), indent=2))
except Exception as e:
    print("Error:", e)
