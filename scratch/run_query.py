import requests
import json
import time

API_BASE_URL = "http://localhost:8000/api/v1"

def run_e2e_query():
    print("=== E2E QUERY VERIFICATION ===")
    
    # 1. Login User
    res = requests.post(f"{API_BASE_URL}/auth/login", data={"username": "user", "password": "user"})
    token = res.json().get("access_token")
    if not token:
        # Register if needed
        requests.post(f"{API_BASE_URL}/auth/register", json={"username": "user", "password": "user", "role": "user"})
        res = requests.post(f"{API_BASE_URL}/auth/login", data={"username": "user", "password": "user"})
        token = res.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Ask Question
    query = "What is the policy term and premium paying term for LIC Jeevan Shagun?"
    print(f"Query: {query}")
    
    start_time = time.time()
    response = requests.post(
        f"{API_BASE_URL}/query",
        headers=headers,
        json={"query": query},
        timeout=180
    )
    
    if response.status_code == 200:
        data = response.json()
        print("\n--- RESPONSE ---")
        answer = data.get("final_answer", "")
        # Safe print for windows console
        print(answer.encode("utf-8", "ignore").decode("utf-8", "ignore"))
        print("\n--- SOURCES ---")
        sources = data.get("sources", [])
        for s in sources:
            print(f"- {s.get('document')} (Page {s.get('page')})")
        print("\n--- TRACE ---")
        trace = data.get("agent_trace", [])
        for t in trace:
            print(f"Agent: {t.get('agent')}, Result: {t.get('result')[:50]}...")
            
    else:
        print(f"Error {response.status_code}: {response.text}")

if __name__ == "__main__":
    run_e2e_query()
