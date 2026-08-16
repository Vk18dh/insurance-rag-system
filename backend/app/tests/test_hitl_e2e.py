import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.database import Base, engine, SessionLocal
from backend.app.models.review_task import ReviewTask, ReviewTaskStatus

@pytest.fixture(scope="module")
def client():
    # Reset database for tests
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c

def test_hitl_workflow_end_to_end(client):
    db = SessionLocal()
    
    # 1. Create test users via API
    client.post("/api/v1/auth/register", json={"username": "hitl_user", "password": "pw", "role": "user"})
    client.post("/api/v1/auth/register", json={"username": "hitl_expert", "password": "pw", "role": "expert"})
    client.post("/api/v1/auth/register", json={"username": "hitl_admin", "password": "pw", "role": "admin"})

    user_token = client.post("/api/v1/auth/login", data={"username": "hitl_user", "password": "pw"}).json()["access_token"]
    expert_token = client.post("/api/v1/auth/login", data={"username": "hitl_expert", "password": "pw"}).json()["access_token"]
    admin_token = client.post("/api/v1/auth/login", data={"username": "hitl_admin", "password": "pw"}).json()["access_token"]

    # 2. User submits query (that will trigger low confidence/fallback)
    query_text = "What is the capital of France?" 
    
    response = client.post(
        "/api/v1/query",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"query": query_text}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["confidence_score"] == 0.0  # Confirmed it triggered the fallback
    
    # Check that a review task was created automatically
    tasks = db.query(ReviewTask).all()
    assert len(tasks) >= 1
    task = tasks[-1] # the latest one
    assert task.status == ReviewTaskStatus.PENDING
    assert "Low confidence detected" in task.reason or "System constraints violated" in task.reason
    assert task.payload["query"] == query_text
    task_id = task.id

    # 3. User tries to access expert API (Should fail)
    res = client.get(
        f"/api/v1/expert/reviews/{task_id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert res.status_code == 403

    # 4. Expert retrieves the task
    res = client.get(
        f"/api/v1/expert/reviews/{task_id}",
        headers={"Authorization": f"Bearer {expert_token}"}
    )
    assert res.status_code == 200
    task_data = res.json()
    assert task_data["id"] == task_id
    assert task_data["payload"]["query"] == query_text

    # 5. Expert corrects the task
    correction_payload = {
        "decision": "CORRECT",
        "corrected_answer": "This is outside the insurance domain.",
        "comment": "User asked about geography."
    }
    res = client.post(
        f"/api/v1/expert/reviews/{task_id}/action",
        headers={"Authorization": f"Bearer {expert_token}"},
        json=correction_payload
    )
    assert res.status_code == 200
    updated_task = res.json()
    assert updated_task["status"] == "CORRECTED"
    assert updated_task["expert_decision"] == "CORRECT"
    assert updated_task["corrected_answer"] == "This is outside the insurance domain."

    # 6. Admin accesses metrics (Verify real data is queried)
    res = client.get(
        "/api/v1/admin/metrics",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res.status_code == 200
    metrics = res.json()
    assert metrics["active_users"] >= 3
    assert metrics["queries_today"] >= 1
    assert metrics["escalation_rate"] > 0
    
    db.close()
