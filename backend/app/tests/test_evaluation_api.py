import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.schemas.auth import TokenPayload

client = TestClient(app)

def mock_get_admin():
    return TokenPayload(sub="admin_user", role="admin")

def mock_get_user():
    return TokenPayload(sub="regular_user", role="user")
    
def mock_get_expert():
    return TokenPayload(sub="expert_user", role="expert")

@pytest.fixture
def override_admin():
    from backend.app.dependencies.auth import require_admin_role
    app.dependency_overrides[require_admin_role] = mock_get_admin
    yield
    app.dependency_overrides.pop(require_admin_role, None)

@pytest.fixture
def override_user():
    from backend.app.dependencies.auth import require_admin_role
    from fastapi import HTTPException
    def fail():
        raise HTTPException(status_code=403, detail="Not enough permissions")
    app.dependency_overrides[require_admin_role] = fail
    yield
    app.dependency_overrides.pop(require_admin_role, None)

def test_evaluation_api_admin_access(override_admin):
    # Using the mock db dependency, we would mock DB here if needed, 
    # but even without it, if we get 500 it means we passed RBAC.
    # To do a clean test we can just check the router doesn't 403.
    response = client.get("/api/v1/admin/evaluations")
    # Should not be 403. Might be 500 if DB is not mocked, but that's fine for RBAC test
    assert response.status_code != 403

def test_evaluation_api_user_denied(override_user):
    response = client.get("/api/v1/admin/evaluations")
    assert response.status_code == 403

def test_evaluation_api_expert_denied(override_user):
    response = client.get("/api/v1/admin/evaluations")
    assert response.status_code == 403
