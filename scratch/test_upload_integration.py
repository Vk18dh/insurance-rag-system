import os
import time
import requests

API_URL = "http://localhost:8000/api/v1"
PDF_PATH = os.path.join("data", "pdfs", "LIC_Jeevan_Shagun_Policy_inside_r.pdf")

def test_integration():
    # 1. Login as Admin
    print("Logging in as Admin...")
    res = requests.post(f"{API_URL}/auth/login", data={"username": "admin", "password": "admin"})
    admin_token = res.json()["access_token"]
    
    # 2. Upload Document
    print("Uploading PDF...")
    headers = {"Authorization": f"Bearer {admin_token}"}
    with open(PDF_PATH, "rb") as f:
        files = {"file": ("test_policy.pdf", f, "application/pdf")}
        data = {"document_name": "Test Integration Policy", "document_type": "Policy"}
        res = requests.post(f"{API_URL}/admin/documents", headers=headers, files=files, data=data)
    
    assert res.status_code == 202
    doc_id = res.json()["id"]
    print(f"Uploaded successfully. Document ID: {doc_id}")
    
    # 3. Wait for processing to complete
    print("Waiting for ingestion to complete (polling)...")
    status = "PROCESSING"
    timeout = 180
    start = time.time()
    
    while status in ["PENDING", "PROCESSING"]:
        if time.time() - start > timeout:
            print("Timeout waiting for ingestion.")
            break
        
        time.sleep(5)
        res = requests.get(f"{API_URL}/admin/documents", headers=headers)
        docs = res.json()
        doc = next((d for d in docs if d["id"] == doc_id), None)
        status = doc["status"]
        print(f"Status: {status}")
    
    if status != "COMPLETED":
        print(f"Ingestion failed with status: {status}")
        if doc.get("error_message"):
            print(f"Error: {doc['error_message']}")
        return

    print("Ingestion COMPLETED successfully.")

    # 4. Login as User
    print("Registering and logging in as User...")
    requests.post(f"{API_URL}/auth/register", json={"username": "upload_test_user", "password": "Password123!", "role": "user"})
    res = requests.post(f"{API_URL}/auth/login", data={"username": "upload_test_user", "password": "Password123!"})
    user_token = res.json()["access_token"]
    
    # 5. Query the newly uploaded policy
    print("Querying for information from the policy...")
    headers = {"Authorization": f"Bearer {user_token}", "Content-Type": "application/json"}
    query_data = {"query": "What is Jeevan Shagun?"}
    
    res = requests.post(f"{API_URL}/query", headers=headers, json=query_data)
    answer = res.json()
    print("Query Answer:")
    print(answer.get("final_answer"))
    print("Sources:")
    for s in answer.get("sources", []):
        print(f"- {s.get('document')}")

if __name__ == "__main__":
    test_integration()
