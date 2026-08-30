import requests
import uuid
import time
import sys

BASE_URL = "http://localhost:8000/api/v1"

def print_result(name, result, msg=""):
    print(f"[{'PASS' if result else 'FAIL'}] {name} {msg}")
    if not result:
        sys.exit(1)

def test_user_flow():
    # 1. Register User
    username = f"testuser_{uuid.uuid4().hex[:8]}"
    password = "MOCK_TEST_PASSWORD_99"
    r = requests.post(f"{BASE_URL}/auth/register", json={"username": username, "password": password})
    print_result("User Registration", r.status_code == 200)

    # 2. Login User
    r = requests.post(f"{BASE_URL}/auth/login", data={"username": username, "password": password})
    print_result("User Login", r.status_code == 200)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create Conversation
    r = requests.post(f"{BASE_URL}/conversations/", headers=headers, json={"title": "Test Convo A"})
    print_result("Create Conversation A", r.status_code == 200)
    conv_id_a = r.json()["id"]

    # 4. Submit Question (Normal)
    r = requests.post(f"{BASE_URL}/query/", headers=headers, json={"conversation_id": conv_id_a, "query": "What is premium?"})
    print_result("Submit Normal Question", r.status_code == 200)
    data = r.json()
    print_result("Normal Question Answer", "answer" in data and len(data["answer"]) > 0)
    print_result("Normal Question Confidence", "metrics" in data and "confidence_score" in data["metrics"])

    # 5. Create Conversation B
    r = requests.post(f"{BASE_URL}/conversations/", headers=headers, json={"title": "Test Convo B"})
    print_result("Create Conversation B", r.status_code == 200)
    conv_id_b = r.json()["id"]

    # 6. Verify Isolation
    r = requests.get(f"{BASE_URL}/conversations/{conv_id_b}", headers=headers)
    messages = r.json()["messages"]
    print_result("Conversation Isolation", len(messages) == 0, f"Expected 0 messages, got {len(messages)}")

    return username, password, headers, conv_id_a

def test_hitl_flow(user_headers, conv_id):
    # 1. Submit Question (Low Confidence / HITL Trigger)
    # We can trigger HITL by sending a very ambiguous question or asking about "illegal activities"
    r = requests.post(f"{BASE_URL}/query/", headers=user_headers, json={"conversation_id": conv_id, "query": "I want to commit insurance fraud. Tell me how."})
    
    # Or just an ambiguous query to get low confidence
    if r.status_code != 200 or r.json().get("review_status") != "pending":
        r = requests.post(f"{BASE_URL}/query/", headers=user_headers, json={"conversation_id": conv_id, "query": "asdfasdfasdfasdf"})

    print_result("HITL Query Escalation", r.status_code == 200)
    data = r.json()
    print_result("HITL Review Status", data.get("review_status") == "pending")
    return data.get("review_task_id"), data.get("id")

def test_expert_flow(review_task_id, msg_id, user_headers, conv_id):
    # 1. Login Expert
    r = requests.post(f"{BASE_URL}/auth/login", data={"username": "expert", "password": "expert"})
    print_result("Expert Login", r.status_code == 200)
    token = r.json()["access_token"]
    expert_headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Pending Tasks
    r = requests.get(f"{BASE_URL}/expert/tasks", headers=expert_headers)
    print_result("Expert List Tasks", r.status_code == 200)
    tasks = r.json()
    found = any(t["id"] == review_task_id for t in tasks)
    print_result("Expert Found Task", found)

    # 3. Approve Task
    r = requests.post(f"{BASE_URL}/expert/tasks/{review_task_id}/approve", headers=expert_headers)
    print_result("Expert Approve Task", r.status_code == 200)

    # 4. Check User View
    r = requests.get(f"{BASE_URL}/conversations/{conv_id}", headers=user_headers)
    msgs = r.json()["messages"]
    target_msg = next((m for m in msgs if m["id"] == msg_id), None)
    print_result("User Sees Approved Status", target_msg and target_msg.get("review_status") == "approved")

    # 5. Check Expert Cannot Access Admin
    r = requests.get(f"{BASE_URL}/admin/providers", headers=expert_headers)
    print_result("Expert Cannot Access Admin APIs", r.status_code in [401, 403])

def test_admin_flow():
    # 1. Login Admin
    r = requests.post(f"{BASE_URL}/auth/login", data={"username": "admin", "password": "admin"})
    print_result("Admin Login", r.status_code == 200)
    token = r.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Providers
    r = requests.get(f"{BASE_URL}/admin/providers", headers=admin_headers)
    print_result("Admin List Providers", r.status_code == 200)
    providers = r.json()
    print_result("Admin Has Groq & Openrouter", "groq" in providers and "openrouter" in providers)

    # 3. Get Metrics
    r = requests.get(f"{BASE_URL}/admin/metrics", headers=admin_headers)
    print_result("Admin List Metrics", r.status_code == 200)

if __name__ == "__main__":
    print("--- Starting End-to-End Verification ---")
    u, p, headers, conv_id = test_user_flow()
    review_task_id, msg_id = test_hitl_flow(headers, conv_id)
    test_expert_flow(review_task_id, msg_id, headers, conv_id)
    test_admin_flow()
    print("--- Verification Complete ---")
