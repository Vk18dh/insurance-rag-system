import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.dependencies.auth import get_current_user, require_admin_role
import io

def test_user_cannot_access_documents():
    # Override auth to simulate standard user
    app.dependency_overrides[require_admin_role] = lambda: None # This will fail dependency validation since require_admin_role actually throws 403, but here we can just mock the 403 or use a client with user token.
    # Actually, a better way is to test the actual endpoint with a user token.

    client = TestClient(app)
    
    # login as user
    response = client.post("/api/v1/auth/login", data={"username": "user", "password": "user"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    get_res = client.get("/api/v1/admin/documents", headers=headers)
    assert get_res.status_code == 403
    
    post_res = client.post("/api/v1/admin/documents", headers=headers, files={"file": ("test.pdf", b"pdf data", "application/pdf")})
    assert post_res.status_code == 403

def test_admin_can_access_documents():
    client = TestClient(app)
    
    # login as admin
    response = client.post("/api/v1/auth/login", data={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    get_res = client.get("/api/v1/admin/documents", headers=headers)
    assert get_res.status_code == 200
    assert isinstance(get_res.json(), list)

def test_upload_invalid_file_extension():
    client = TestClient(app)
    
    response = client.post("/api/v1/auth/login", data={"username": "admin", "password": "admin"})
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
