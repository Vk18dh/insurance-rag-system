import requests
import json
import sys
import time

BASE_URL = "http://localhost:8000/api/v1"

def print_result(name, passed, details=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} | {name}")
    if details:
        print(f"  {details}")

def test_health():
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=5)
        if r.status_code == 200:
            print_result("Health Check", True, r.json())
            return True
        else:
            print_result("Health Check", False, r.text)
            return False
    except Exception as e:
        print_result("Health Check", False, str(e))
        return False

def test_auth_and_query():
    # Register
    try:
        # random user
        username = f"user_{int(time.time())}"
        r = requests.post(f"{BASE_URL}/auth/register", json={
            "username": username,
            "password": "password",
            "email": f"{username}@example.com",
            "full_name": "Test User",
            "role": "user"
        })
        if r.status_code != 200:
            print_result("Registration", False, r.text)
            return
        print_result("Registration", True, f"User {username} registered")
        
        # Login
        r = requests.post(f"{BASE_URL}/auth/login", data={"username": username, "password": "password"})
        if r.status_code != 200:
            print_result("Login", False, r.text)
            return
        token = r.json().get("access_token")
        print_result("Login", True, "Token received")
        
        headers = {"Authorization": f"Bearer {token}"}
        
        # Create Conversation A
        r = requests.post(f"{BASE_URL}/conversations/", json={"title": "Test Conv A"}, headers=headers)
        if r.status_code != 200:
            print_result("Create Conversation A", False, r.text)
            return
        conv_a_id = r.json().get("id")
        print_result("Create Conversation A", True, f"ID: {conv_a_id}")
        
        # Query 
        query_payload = {
            "query": "What are the death benefits under LIC Bima Jyoti policy?",
            "conversation_id": conv_a_id
        }
        print("Sending full RAG query. This may take 10-30 seconds depending on LLM...")
        r = requests.post(f"{BASE_URL}/query", json=query_payload, headers=headers)
        if r.status_code != 200:
            print_result("Full RAG E2E Query", False, r.text)
            return
        resp = r.json()
        print_result("Full RAG E2E Query", True, "Response received")
        
        # Verify schema
        print("Final Answer:", resp.get("final_answer"))
        print("Confidence:", resp.get("confidence_score"))
        sources = resp.get("sources", [])
        print("Sources count:", len(sources))
        for s in sources:
            print(f" - {s.get('document')} p.{s.get('page')}")
        
        print("\nAll integration tests finished.")
    except Exception as e:
        print_result("Auth & Query Flow", False, str(e))

if __name__ == "__main__":
    if test_health():
        test_auth_and_query()
