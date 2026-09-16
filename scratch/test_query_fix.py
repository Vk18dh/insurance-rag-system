import requests
import json
import time

def test_query():
    # 1. Register a test user
    print("Registering test user...")
    res = requests.post("http://localhost:8000/api/v1/auth/register", json={
        "username": "testuser1234",
        "password": "testuser1234"
    })
    
    # 2. Login
    print("Logging in...")
    res = requests.post("http://localhost:8000/api/v1/auth/login", data={
        "username": "testuser1234",
        "password": "testuser1234"
    })
    token = res.json().get("access_token")
    if not token:
        print("Login failed:", res.text)
        return
        
    headers = {"Authorization": f"Bearer {token}"}
    
    # 3. Submit query
    print("Submitting query...")
    start = time.time()
    res = requests.post("http://localhost:8000/api/v1/query", json={
        "query": "What is the waiting period for the basic health insurance?"
    }, headers=headers)
    
    end = time.time()
    print(f"Query returned in {end - start:.2f} seconds")
    print(f"Status: {res.status_code}")
    print(json.dumps(res.json(), indent=2))

if __name__ == "__main__":
    test_query()
