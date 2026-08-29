import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.db.database import Base, engine, SessionLocal
from backend.app.models.review_task import ReviewTask
from backend.app.dependencies.agents import get_agent_orchestrator

@pytest.fixture(scope="module")
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        # Register and login user
        c.post("/api/v1/auth/register", json={"username": "sep_user", "password": "pw", "role": "user"})
        token = c.post("/api/v1/auth/login", data={"username": "sep_user", "password": "pw"}).json()["access_token"]
        yield c, token

class MockMetadata:
    def __init__(self, confidence):
        self.confidence = confidence

class MockFinalResponse:
    def __init__(self, answer, citations, warnings, confidence):
        self.direct_answer = answer
        self.citations = citations
        self.warnings = warnings
        self.metadata = MockMetadata(confidence)

class MockSharedContext:
    def __init__(self, final_resp):
        self.final_response = final_resp

class MockOrchestratorResult:
    def __init__(self, final_resp, errors=None):
        self.shared_context = MockSharedContext(final_resp)
        self.errors = errors or []
        self.request_id = "test-req-id"

def test_genuine_low_confidence_creates_hitl(client):
    c, token = client
    
    # Mock orchestrator to return low confidence
    def override_orchestrator():
        class DummyOrchestrator:
            def orchestrate(self, query, conversation_id=None):
                return MockOrchestratorResult(
                    MockFinalResponse("Uncertain answer", [], [], 0.4) # 0.4 is < 0.70 threshold
                )
        return DummyOrchestrator()
        
    app.dependency_overrides[get_agent_orchestrator] = override_orchestrator
    
    db = SessionLocal()
    initial_tasks = db.query(ReviewTask).count()
    
    response = c.post(
        "/api/v1/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "A highly ambiguous query"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["confidence_score"] == 0.4
    assert data["review_task_id"] is not None
    
    final_tasks = db.query(ReviewTask).count()
    assert final_tasks == initial_tasks + 1
    
    app.dependency_overrides.clear()
    db.close()

def test_infrastructure_failure_prevents_hitl(client):
    c, token = client
    
    # Mock orchestrator to simulate total provider exhaustion
    def override_orchestrator():
        class DummyOrchestrator:
            def orchestrate(self, query, conversation_id=None):
                return MockOrchestratorResult(
                    None, 
                    errors=["Providers exhausted: all LLM adapters failed"]
                )
        return DummyOrchestrator()
        
    app.dependency_overrides[get_agent_orchestrator] = override_orchestrator
    
    db = SessionLocal()
    initial_tasks = db.query(ReviewTask).count()
    
    response = c.post(
        "/api/v1/query",
        headers={"Authorization": f"Bearer {token}"},
        json={"query": "Query during outage"}
    )
    
    # Must be 503 Service Unavailable, NOT 200 with low confidence
    assert response.status_code == 503
    assert "LLM Provider Service Unavailable" in response.json()["detail"]
    
    final_tasks = db.query(ReviewTask).count()
    # Must NOT create a ReviewTask
    assert final_tasks == initial_tasks
    
    app.dependency_overrides.clear()
    db.close()
