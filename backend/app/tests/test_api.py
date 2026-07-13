from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_auth_login_success():
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin_user", "password": "password"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"

def test_auth_login_failure():
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "admin_user", "password": "wrong_password"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

def test_query_endpoint_requires_auth():
    response = client.post(
        "/api/v1/query",
        json={"query": "Test"}
    )
    # HTTP 401 Unauthorized expected due to lacking bearer token
    assert response.status_code == 401

def test_query_endpoint_success_with_auth():
    # 1. Login
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": "expert_user", "password": "password"}
    )
    token = login_resp.json()["access_token"]
    
    # 2. Query
    response = client.post(
        "/api/v1/query",
        json={"query": "What are mature benefits of LIC?"},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "query_id" in data
    assert "final_answer" in data
    assert "confidence_score" in data
