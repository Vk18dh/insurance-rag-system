import requests
import time
import sys

API_BASE_URL = "http://localhost:8000/api/v1"

def run():
    print("=== REAL LLM QUERY VERIFICATION ===")
    
    # 1. Login User
    res = requests.post(f"{API_BASE_URL}/auth/login", data={"username": "user", "password": "user"})
    if res.status_code != 200:
        requests.post(f"{API_BASE_URL}/auth/register", json={"username": "user", "password": "user", "role": "user"})
        res = requests.post(f"{API_BASE_URL}/auth/login", data={"username": "user", "password": "user"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    query = "What is the premium paying term for LIC Jeevan Shagun?"
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
        print("Status: 200 OK")
        print("Final Answer:", data.get("final_answer", ""))
        trace = data.get("agent_trace", [])
        print("\n--- TRACE ---")
        for t in trace:
            print(f"Agent: {t.get('agent')}, Result: {t.get('result')[:50]}...")
            
        print("\nSUCCESS: Real LLM query executed successfully.")
        
    else:
        print(f"Error {response.status_code}: {response.text}")
        sys.exit(1)

if __name__ == "__main__":
    run()
