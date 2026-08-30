import os
import requests
import json
import time
import pickle

API_URL = "http://localhost:8000/api/v1"
PDF_PATH = os.path.join("data", "pdfs", "LIC_Jeevan_Shagun_Policy_inside_r.pdf")

def run_verifications():
    results = {}
    
    print("=== 1. POLICY DOCUMENT INGESTION ===")
    res = requests.post(f"{API_URL}/auth/login", data={"username": "admin", "password": "admin"})
    admin_token = res.json()["access_token"]
    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    
    print("Uploading PDF...")
    with open(PDF_PATH, "rb") as f:
        files = {"file": ("test_policy.pdf", f, "application/pdf")}
        data = {"document_name": "Verification Policy", "document_type": "Policy"}
        res = requests.post(f"{API_URL}/admin/documents", headers=headers_admin, files=files, data=data)
    
    assert res.status_code == 202, f"Upload failed: {res.text}"
    doc_id = res.json()["id"]
    print(f"Document ID: {doc_id}")
    
    status = "PROCESSING"
    timeout = 180
    start = time.time()
    while status in ["PENDING", "PROCESSING"]:
        if time.time() - start > timeout:
            print("Timeout waiting for ingestion.")
            break
        time.sleep(5)
        res = requests.get(f"{API_URL}/admin/documents", headers=headers_admin)
        doc = next((d for d in res.json() if d["id"] == doc_id), None)
        status = doc["status"]
        print(f"Status: {status}")
        
    print(f"Ingestion {status}")

if __name__ == "__main__":
    run_verifications()
