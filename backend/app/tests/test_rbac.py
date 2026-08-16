import pytest

def test_user_cannot_access_expert_admin(client):
    client.post("/api/v1/auth/register", json={"username": "user1", "password": "pw", "role": "user"})
    token = client.post("/api/v1/auth/login", data={"username": "user1", "password": "pw"}).json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # User can access user routes
    res1 = client.get("/api/v1/conversations/", headers=headers)
    assert res1.status_code == 200
    
    # User denied expert
    res2 = client.get("/api/v1/expert/dashboard", headers=headers)
    assert res2.status_code == 403
    
    # User denied admin
    res3 = client.get("/api/v1/admin/dashboard", headers=headers)
    assert res3.status_code == 403

def test_expert_can_access_expert_but_not_admin(client):
    client.post("/api/v1/auth/register", json={"username": "exp1", "password": "pw", "role": "expert"})
    token = client.post("/api/v1/auth/login", data={"username": "exp1", "password": "pw"}).json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Expert allowed expert
    res1 = client.get("/api/v1/expert/dashboard", headers=headers)
    assert res1.status_code == 200
    
    # Expert denied admin
    res2 = client.get("/api/v1/admin/dashboard", headers=headers)
    assert res2.status_code == 403

def test_admin_can_access_all(client):
    client.post("/api/v1/auth/register", json={"username": "adm1", "password": "pw", "role": "admin"})
    token = client.post("/api/v1/auth/login", data={"username": "adm1", "password": "pw"}).json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}
    
    res1 = client.get("/api/v1/admin/dashboard", headers=headers)
    assert res1.status_code == 200
    
    res2 = client.get("/api/v1/expert/dashboard", headers=headers)
    assert res2.status_code == 200
