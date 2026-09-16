import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.app.services.audit_service import AuditService
from backend.app.models.audit import SecurityAuditLog
from backend.app.tests.conftest import TestingSessionLocal
from backend.app.models.user import Role
from datetime import datetime

def get_auth_headers(client, username, password):
    client.post("/api/v1/auth/register", json={"username": username, "password": password, "role": "user"})
    resp = client.post("/api/v1/auth/login", data={"username": username, "password": password})
    if resp.status_code != 200:
        return {}
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def get_auth_headers_role(client, username, password, role):
    client.post("/api/v1/auth/register", json={"username": username, "password": password, "role": role})
    resp = client.post("/api/v1/auth/login", data={"username": username, "password": password})
    if resp.status_code != 200:
        return {}
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_audit_immutability(client):
    # Verify there are no update or delete endpoints exposed
    headers = get_auth_headers_role(client, "admin_immut", "pass123", "admin")
    
    # Try PUT, DELETE, PATCH
    assert client.put("/api/v1/admin/audit/123", headers=headers).status_code == 404
    assert client.delete("/api/v1/admin/audit/123", headers=headers).status_code == 404
    assert client.patch("/api/v1/admin/audit/123", headers=headers).status_code == 404

def test_audit_rbac(client):
    # Create an admin, user, and expert
    headers_user = get_auth_headers_role(client, "audit_user1", "pass", "user")
    headers_expert = get_auth_headers_role(client, "audit_expert1", "pass", "expert")
    headers_admin = get_auth_headers_role(client, "audit_admin1", "pass", "admin")
    
    # User should get 403
    resp_user = client.get("/api/v1/admin/audit", headers=headers_user)
    assert resp_user.status_code == 403
    
    # Expert should get 403
    resp_expert = client.get("/api/v1/admin/audit", headers=headers_expert)
    assert resp_expert.status_code == 403
    
    # Admin should get 200
    resp_admin = client.get("/api/v1/admin/audit", headers=headers_admin)
    assert resp_admin.status_code == 200
    assert "items" in resp_admin.json()

def test_audit_security_no_secrets_stored(db_session):
    # Force an audit log with forbidden keys to ensure they are redacted
    AuditService.log_event(
        action="TEST_SECRETS",
        safe_metadata={"password": "supersecretpassword", "jwt": "token123", "api_key": "sk-123"}
    )
    db_session.commit()
    
    log = db_session.query(SecurityAuditLog).filter(SecurityAuditLog.action == "TEST_SECRETS").first()
    assert log is not None
    assert log.safe_metadata["password"] == "[REDACTED]"
    assert log.safe_metadata["jwt"] == "[REDACTED]"
    assert log.safe_metadata["api_key"] == "[REDACTED]"
    assert "supersecretpassword" not in str(log.safe_metadata)
    assert "token123" not in str(log.safe_metadata)

def test_audit_integration_login(client, db_session):
    client.post("/api/v1/auth/register", json={"username": "logintest", "password": "abc", "role": "user"})
    client.post("/api/v1/auth/login", data={"username": "logintest", "password": "abc"})
    db_session.commit()
    
    logs = db_session.query(SecurityAuditLog).filter(SecurityAuditLog.action == "LOGIN_SUCCESS").all()
    assert len(logs) > 0
    
    client.post("/api/v1/auth/login", data={"username": "logintest", "password": "wrongpassword"})
    db_session.commit()
    logs_fail = db_session.query(SecurityAuditLog).filter(SecurityAuditLog.action == "LOGIN_FAILURE").all()
    assert len(logs_fail) > 0

def test_audit_integration_rbac_denied(client, db_session):
    headers = get_auth_headers_role(client, "rbacuser", "pass", "user")
    
    # Trigger 403 by accessing expert dashboard
    client.get("/api/v1/expert/dashboard", headers=headers)
    db_session.commit()
    
    logs = db_session.query(SecurityAuditLog).filter(SecurityAuditLog.action == "RBAC_DENIED").all()
    assert len(logs) > 0

def test_audit_integration_query(client, db_session):
    headers = get_auth_headers_role(client, "queryuser", "pass", "user")
    
    # We patch the orchestrator so it doesn't actually try to run real LLMs
    with patch("backend.app.routers.query.AgentOrchestrator.orchestrate") as mock_orch:
        class MockResponse:
            class MockShared:
                final_response = None
            shared_context = MockShared()
            request_id = "test-req"
            errors = []
        mock_orch.return_value = MockResponse()
        
        client.post("/api/v1/query", json={"query": "test query"}, headers=headers)
    db_session.commit()
    
    logs = db_session.query(SecurityAuditLog).filter(SecurityAuditLog.action == "QUERY_SUBMITTED").all()
    assert len(logs) > 0
    assert logs[0].safe_metadata["query_hash"] != "test query" # Ensure it's hashed
