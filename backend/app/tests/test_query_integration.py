import pytest
from unittest.mock import MagicMock

def test_query_creates_conversation_and_persists_messages(client, monkeypatch):
    # Register and login
    client.post("/api/v1/auth/register", json={"username": "q_user", "password": "pw", "role": "user"})
    token = client.post("/api/v1/auth/login", data={"username": "q_user", "password": "pw"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Mock the AgentOrchestrator to avoid hitting real models
    from phase2.orchestrator.orchestrator import AgentOrchestrator
    from phase2.models.orchestration_result import OrchestrationResult
    
    class MockOrchestrator:
        def orchestrate(self, query, conversation_id):
            result = MagicMock()
            result.request_id = "mock_request_id"
            result.shared_context.final_response.direct_answer = "Mocked answer"
            result.shared_context.final_response.citations = []
            result.shared_context.final_response.warnings = []
            result.shared_context.final_response.metadata.confidence = 0.99
            return result
            
    app_mock_orch = MockOrchestrator()
    
    # Override dependency in app
    from backend.app.main import app
    from backend.app.dependencies.agents import get_agent_orchestrator
    app.dependency_overrides[get_agent_orchestrator] = lambda: app_mock_orch

    # 1. Send query without conversation_id
    res = client.post("/api/v1/query", json={"query": "Hello world"}, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "conversation_id" in data
    conv_id = data["conversation_id"]
    assert data["final_answer"] == "Mocked answer"

    # 2. Check if conversation was created
    res_conv = client.get(f"/api/v1/conversations/{conv_id}", headers=headers)
    assert res_conv.status_code == 200
    
    # 3. Check messages
    res_msg = client.get(f"/api/v1/conversations/{conv_id}/messages", headers=headers)
    assert res_msg.status_code == 200
    msgs = res_msg.json()
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[0]["content"] == "Hello world"
    assert msgs[1]["role"] == "assistant"
    assert msgs[1]["content"] == "Mocked answer"
    
    # 4. Send query with existing conversation_id
    res2 = client.post("/api/v1/query", json={"query": "Follow up", "conversation_id": conv_id}, headers=headers)
    assert res2.status_code == 200
    
    res_msg2 = client.get(f"/api/v1/conversations/{conv_id}/messages", headers=headers)
    msgs2 = res_msg2.json()
    assert len(msgs2) == 4
    
    app.dependency_overrides.clear()
