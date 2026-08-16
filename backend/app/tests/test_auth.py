import pytest
from backend.app.schemas.auth import Role

def test_register_and_login(client):
    # Register
    res = client.post("/api/v1/auth/register", json={
        "username": "testuser",
        "password": "testpassword",
        "role": "user"
    })
    assert res.status_code == 200
    assert res.json()["username"] == "testuser"
    assert res.json()["role"] == "user"

    # Login Success
    res_login = client.post("/api/v1/auth/login", data={
        "username": "testuser",
        "password": "testpassword"
    })
    assert res_login.status_code == 200
    assert "access_token" in res_login.json()
    
def test_login_invalid_password(client):
    client.post("/api/v1/auth/register", json={
        "username": "testuser2",
        "password": "testpassword",
        "role": "user"
    })
    res_login = client.post("/api/v1/auth/login", data={
        "username": "testuser2",
        "password": "wrongpassword"
    })
    assert res_login.status_code == 401

def test_login_unknown_user(client):
    res_login = client.post("/api/v1/auth/login", data={
        "username": "unknown_user",
        "password": "wrongpassword"
    })
    assert res_login.status_code == 401

def test_missing_token_auth(client):
    res = client.get("/api/v1/conversations/")
    assert res.status_code == 401
    
def test_malformed_token_auth(client):
    res = client.get("/api/v1/conversations/", headers={"Authorization": "Bearer not-a-real-token"})
    assert res.status_code == 401
