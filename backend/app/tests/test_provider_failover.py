import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.database import Base, engine, SessionLocal
from backend.app.models.review_task import ReviewTask
from backend.app.dependencies.agents import get_agent_orchestrator
from unittest.mock import patch
from enum import Enum

class MockPhase2Intent(Enum):
    GENERAL_INQUIRY = "general_inquiry"
    UNKNOWN = "unknown"

class MockPhase2Classification(Enum):
    FACTUAL = "factual"

class MockResult:
    def __init__(self, request_id="123", direct_answer="", final_response=None, errors=None, shared_context=None):
        self.request_id = request_id
        self.direct_answer = direct_answer
        self.final_response = final_response
        self.errors = errors or []
        self.shared_context = shared_context or self

@pytest.fixture(scope="module")
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c

def test_hitl_test_setup(client):
    client.post("/api/v1/auth/register", json={"username": "testuser", "password": "pw", "role": "user"})

def test_8_provider_failure_no_review_task(client):
    db = SessionLocal()
    initial_task_count = db.query(ReviewTask).count()
    user_token = client.post("/api/v1/auth/login", data={"username": "testuser", "password": "pw"}).json()["access_token"]
    
    # Mock the orchestrator to simulate complete provider exhaustion
    mock_res = MockResult(final_response=None, errors=["Providers exhausted due to API execution failure", "Groq HTTP Error"])
    
    class MockOrchestrator:
        def orchestrate(self, *args, **kwargs):
            return mock_res
            
    app.dependency_overrides[get_agent_orchestrator] = lambda: MockOrchestrator()
    
    response = client.post(
        "/api/v1/query",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"query": "Test query provider failure"}
    )
    
    app.dependency_overrides = {}
    
    # Should be a 503 error, not a 200 with 0 confidence
    assert response.status_code == 503
    assert "LLM Provider Service Unavailable" in response.json()["detail"]
    
    # Verify no review task was created
    final_task_count = db.query(ReviewTask).count()
    assert final_task_count == initial_task_count
    db.close()

def test_9_genuine_low_confidence_creates_review_task(client):
    db = SessionLocal()
    initial_task_count = db.query(ReviewTask).count()
    user_token = client.post("/api/v1/auth/login", data={"username": "testuser", "password": "pw"}).json()["access_token"]
    
    # Mock the orchestrator to simulate a real logic failure (e.g., QA constraints)
    mock_res = MockResult(final_response=None, errors=["VerificationResult failed QA upstream constraints"])
    
    class MockOrchestrator:
        def orchestrate(self, *args, **kwargs):
            return mock_res
            
    app.dependency_overrides[get_agent_orchestrator] = lambda: MockOrchestrator()
    
    response = client.post(
        "/api/v1/query",
        headers={"Authorization": f"Bearer {user_token}"},
        json={"query": "Test query low confidence"}
    )
    
    app.dependency_overrides = {}
    
    # Should be a 200 with a fallback answer and 0 confidence
    assert response.status_code == 200
    data = response.json()
    assert data["confidence_score"] == 0.0
    assert "refusing to hallucinate" in data["final_answer"]
    
    # Verify a review task WAS created
    final_task_count = db.query(ReviewTask).count()
    assert final_task_count == initial_task_count + 1
    
    task = db.query(ReviewTask).order_by(ReviewTask.id.desc()).first()
    assert "Low confidence detected" in task.reason or "System constraints violated" in task.reason
    db.close()
