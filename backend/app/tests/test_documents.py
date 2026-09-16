import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.dependencies.auth import get_current_user, require_admin_role
import io

def test_user_cannot_access_documents(client):
    # register and login as user
    client.post("/api/v1/auth/register", json={"username": "testuser_doc", "password": "userpass", "role": "user"})
    response = client.post("/api/v1/auth/login", data={"username": "testuser_doc", "password": "userpass"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    get_res = client.get("/api/v1/admin/documents", headers=headers)
    assert get_res.status_code == 403
    
    post_res = client.post("/api/v1/admin/documents", headers=headers, files={"file": ("test.pdf", b"pdf data", "application/pdf")})
    assert post_res.status_code == 403

def test_admin_can_access_documents(client):
    # register and login as admin
    client.post("/api/v1/auth/register", json={"username": "test_admin_doc", "password": "adminpass", "role": "admin"})
    response = client.post("/api/v1/auth/login", data={"username": "test_admin_doc", "password": "adminpass"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    get_res = client.get("/api/v1/admin/documents", headers=headers)
    assert get_res.status_code == 200
    assert isinstance(get_res.json(), list)

def test_upload_invalid_file_extension(client):
    # register and login as admin
    client.post("/api/v1/auth/register", json={"username": "test_admin_doc2", "password": "adminpass2", "role": "admin"})
    response = client.post("/api/v1/auth/login", data={"username": "test_admin_doc2", "password": "adminpass2"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    post_res = client.post(
        "/api/v1/admin/documents",
        headers=headers,
        data={"document_name": "Test Document"},
        files={"file": ("test.txt", b"not a pdf", "text/plain")}
    )
    
    assert post_res.status_code == 400
    assert "Only PDF files are supported" in post_res.json()["detail"]
