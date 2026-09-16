import pytest
from unittest.mock import patch, MagicMock
from backend.app.services.evaluation_service import EvaluationService
from backend.app.models.evaluation import EvaluationRun, EvaluationCaseResult
from backend.app.db.database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("sqlite:///:memory:")
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_evaluation_isolation_and_execution(db_session):
    # Create a test run
    run = EvaluationRun(id="test-run", dataset_version="1.0", evaluator_model="qwen2.5:3b")
    db_session.add(run)
    db_session.commit()
    
    svc = EvaluationService(db_session)
    
    # Mock dataset
    svc.load_dataset = MagicMock(return_value={
        "version": "1.0",
        "cases": [
            {
                "id": "CASE-1",
                "category": "in_domain",
                "query": "Test query",
                "expected_behavior": "Should answer",
                "hitl_expected": False
            }
        ]
    })
    
    # Mock orchestrator
    mock_orchestrator = MagicMock()
    mock_result = MagicMock()
    mock_result.shared_context.final_response.direct_answer = "Mocked answer"
    mock_result.shared_context.final_response.citations = []
    mock_result.shared_context.final_response.warnings = ["Low confidence"]
    mock_result.shared_context.final_response.metadata.confidence = 0.5
    mock_orchestrator.orchestrate.return_value = mock_result
    
    svc._create_isolated_orchestrator = MagicMock(return_value=mock_orchestrator)
    
    # Mock Ollama evaluator
    svc._call_ollama_evaluator = MagicMock(return_value={
        "success": True,
        "data": {
            "retrieval_score": 0.9,
            "relevance_score": 0.8,
            "faithfulness_score": 0.7,
            "hallucination_score": 0.1,
            "citation_score": 0.5,
            "pass": True,
            "evaluator_reason": "Looks good"
        },
        "raw": "{}",
        "latency": 150.0
    })
    
    # Execute the background task synchronously for testing
    svc.run_evaluation_background("test-run", test_db=db_session)
    
    db_session.refresh(run)
    assert run.status == "COMPLETED"
    assert run.total_cases == 1
    assert run.passed_cases == 1
    
    results = db_session.query(EvaluationCaseResult).filter_by(run_id="test-run").all()
    assert len(results) == 1
    res = results[0]
    
    assert res.passed is True
    assert res.hitl_actual is True  # Because confidence 0.5 < 0.8 and warnings exist
    assert res.retrieval_score == 0.9
    
    # Crucially verify orchestrator was called with no conversation_id, ensuring isolation
    mock_orchestrator.orchestrate.assert_called_once_with("Test query", conversation_id=None)
