import requests

API_BASE_URL = "http://localhost:8000/api/v1"

def test_hitl():
    print("=== HITL REGRESSION VERIFICATION ===")
    res = requests.post(f"{API_BASE_URL}/auth/login", data={"username": "user", "password": "user"})
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Send highly out of domain query
    query = "What is the capital of Mars and how does it affect black hole entropy?"
    print(f"Query: {query}")
    
    res = requests.post(
        f"{API_BASE_URL}/query",
        headers=headers,
        json={"query": query},
        timeout=180
    )
    
    if res.status_code == 200:
        data = res.json()
        print("Status Code: 200")
        print("Confidence:", data.get("confidence_score"))
        if data.get("review_task_id"):
            print("HITL SUCCESS: Review Task Created.")
            print(f"Task ID: {data['review_task_id']}")
        else:
            print("HITL FAILURE: No review task created.")
    else:
        print(f"Error {res.status_code}: {res.text}")

if __name__ == "__main__":
    test_hitl()
