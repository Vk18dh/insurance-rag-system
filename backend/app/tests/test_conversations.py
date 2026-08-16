import pytest

def test_conversation_isolation(client):
    # User A
    client.post("/api/v1/auth/register", json={"username": "userA", "password": "pw", "role": "user"})
    token_a = client.post("/api/v1/auth/login", data={"username": "userA", "password": "pw"}).json()["access_token"]
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User B
    client.post("/api/v1/auth/register", json={"username": "userB", "password": "pw", "role": "user"})
    token_b = client.post("/api/v1/auth/login", data={"username": "userB", "password": "pw"}).json()["access_token"]
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates a conversation
    res = client.post("/api/v1/conversations/", json={"title": "Test Title"}, headers=headers_a)
    assert res.status_code == 200
    conv_id = res.json()["id"]

    # User A lists conversations and sees it
    res = client.get("/api/v1/conversations/", headers=headers_a)
    assert len(res.json()) == 1
    assert res.json()[0]["id"] == conv_id

    # User B lists conversations and sees 0
    res = client.get("/api/v1/conversations/", headers=headers_b)
    assert len(res.json()) == 0

    # User B tries to get User A's conversation
    res = client.get(f"/api/v1/conversations/{conv_id}", headers=headers_b)
    assert res.status_code == 404
    
    # User B tries to get User A's messages
    res = client.get(f"/api/v1/conversations/{conv_id}/messages", headers=headers_b)
    assert res.status_code == 404

def test_invalid_conversation_id(client):
    client.post("/api/v1/auth/register", json={"username": "userC", "password": "pw", "role": "user"})
    token = client.post("/api/v1/auth/login", data={"username": "userC", "password": "pw"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/v1/conversations/invalid-uuid-format", headers=headers)
    assert res.status_code == 404
