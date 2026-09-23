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

def test_A_supported_retriever_fails_system_refuses(db_session):
    # Dataset says corpus_support=PRESENT. System refuses. Expected: PASS=False.
    run = EvaluationRun(id="test-run-2", dataset_version="1.0", evaluator_model="qwen2.5:3b")
    db_session.add(run)
    db_session.commit()
    
    svc = EvaluationService(db_session)
    svc.load_dataset = MagicMock(return_value={"version": "1.0", "cases": [{"id": "Test-A", "category": "in_domain", "query": "Q", "expected_behavior": "E", "corpus_support": "present"}]})
    
    mock_orch = MagicMock()
    mock_res = MagicMock()
    mock_res.shared_context.final_response.direct_answer = "I could not find related evidence"
    mock_res.shared_context.final_response.citations = []
    mock_res.shared_context.final_response.warnings = []
    mock_orch.orchestrate.return_value = mock_res
    svc._create_isolated_orchestrator = MagicMock(return_value=mock_orch)
    
    # Judge will fail it based on prompt rules
    svc._call_ollama_evaluator = MagicMock(return_value={"success": True, "data": {"pass": False}, "raw": "", "latency": 1.0})
    
    svc.run_evaluation_background("test-run-2", test_db=db_session)
    res = db_session.query(EvaluationCaseResult).filter_by(case_id="Test-A").first()
    assert res.passed is False

def test_B_unsupported_system_refuses(db_session):
    # Dataset says corpus_support=UNAVAILABLE. System refuses. Expected: PASS.
    run = EvaluationRun(id="test-run-3", dataset_version="1.0", evaluator_model="qwen2.5:3b")
    db_session.add(run)
    db_session.commit()
    
    svc = EvaluationService(db_session)
    svc.load_dataset = MagicMock(return_value={"version": "1.0", "cases": [{"id": "Test-B", "category": "in_domain", "query": "Q", "expected_behavior": "safe_refusal", "corpus_support": "unavailable"}]})
    
    mock_orch = MagicMock()
    mock_res = MagicMock()
    mock_res.shared_context.final_response.direct_answer = "I could not find related evidence"
    mock_res.shared_context.final_response.citations = []
    mock_res.shared_context.final_response.warnings = []
    mock_orch.orchestrate.return_value = mock_res
    svc._create_isolated_orchestrator = MagicMock(return_value=mock_orch)
    
    # Judge passes
    svc._call_ollama_evaluator = MagicMock(return_value={"success": True, "data": {"pass": True}, "raw": "", "latency": 1.0})
    
    svc.run_evaluation_background("test-run-3", test_db=db_session)
    res = db_session.query(EvaluationCaseResult).filter_by(case_id="Test-B").first()
    assert res.passed is True
    # Verify metrics are N/A
    assert res.retrieval_score is None
    assert getattr(res, "faithfulness_score", 1.0) == 1.0
    assert res.citation_score is None

def test_C_unsupported_system_answers(db_session):
    run = EvaluationRun(id="test-run-4", dataset_version="1.0", evaluator_model="qwen2.5:3b")
    db_session.add(run)
    db_session.commit()
    
    svc = EvaluationService(db_session)
    svc.load_dataset = MagicMock(return_value={"version": "1.0", "cases": [{"id": "Test-C", "category": "in_domain", "query": "Valid test query", "expected_behavior": "safe_refusal", "corpus_support": "unavailable"}]})
    
    mock_orch = MagicMock()
    mock_res = MagicMock()
    mock_res.shared_context.final_response.direct_answer = "Factual answer"
    mock_res.shared_context.final_response.citations = []
    mock_res.shared_context.final_response.warnings = []
    mock_orch.orchestrate.return_value = mock_res
    svc._create_isolated_orchestrator = MagicMock(return_value=mock_orch)
    
    # Judge fails it
    svc._call_ollama_evaluator = MagicMock(return_value={"success": True, "data": {"pass": False}, "raw": "", "latency": 1.0})
    
    from unittest.mock import patch
    from backend.app.services.guardrail_service import GuardrailService
    with patch.object(GuardrailService, "check_input", return_value=(True, "")), \
         patch.object(GuardrailService, "check_output", return_value=(True, "")):
        svc.run_evaluation_background("test-run-4", test_db=db_session)
    res = db_session.query(EvaluationCaseResult).filter_by(case_id="Test-C").first()
    assert res.passed is False

def test_D_supported_system_answers(db_session):
    run = EvaluationRun(id="test-run-5", dataset_version="1.0", evaluator_model="qwen2.5:3b")
    db_session.add(run)
    db_session.commit()
    
    svc = EvaluationService(db_session)
    svc.load_dataset = MagicMock(return_value={"version": "1.0", "cases": [{"id": "Test-D", "category": "in_domain", "query": "Q", "expected_behavior": "E", "corpus_support": "present"}]})
    
    mock_orch = MagicMock()
    mock_res = MagicMock()
    mock_res.shared_context.final_response.direct_answer = "Correct answer"
    
    cit = MagicMock()
    cit.source_document = "Doc"
    cit.page_number = 1
    mock_res.shared_context.final_response.citations = [cit]
    mock_res.shared_context.final_response.warnings = []
    mock_orch.orchestrate.return_value = mock_res
    svc._create_isolated_orchestrator = MagicMock(return_value=mock_orch)
    
    svc._call_ollama_evaluator = MagicMock(return_value={"success": True, "data": {"pass": True, "retrieval_score": 1.0, "citation_score": 1.0}, "raw": "", "latency": 1.0})
    
    svc.run_evaluation_background("test-run-5", test_db=db_session)
    res = db_session.query(EvaluationCaseResult).filter_by(case_id="Test-D").first()
    assert res.passed is True
    assert res.retrieval_score == 1.0

def test_E_supported_system_answers_incorrectly(db_session):
    run = EvaluationRun(id="test-run-6", dataset_version="1.0", evaluator_model="qwen2.5:3b")
    db_session.add(run)
    db_session.commit()
    
    svc = EvaluationService(db_session)
    svc.load_dataset = MagicMock(return_value={"version": "1.0", "cases": [{"id": "Test-E", "category": "in_domain", "query": "Q", "expected_behavior": "E", "corpus_support": "present"}]})
    
    mock_orch = MagicMock()
    mock_res = MagicMock()
    mock_res.shared_context.final_response.direct_answer = "Wrong answer"
    mock_res.shared_context.final_response.citations = []
    mock_res.shared_context.final_response.warnings = []
    mock_orch.orchestrate.return_value = mock_res
    svc._create_isolated_orchestrator = MagicMock(return_value=mock_orch)
    
    svc._call_ollama_evaluator = MagicMock(return_value={"success": True, "data": {"pass": False}, "raw": "", "latency": 1.0})
    
    svc.run_evaluation_background("test-run-6", test_db=db_session)
    res = db_session.query(EvaluationCaseResult).filter_by(case_id="Test-E").first()
    assert res.passed is False

def test_F_unsupported_system_invents_citation(db_session):
    run = EvaluationRun(id="test-run-7", dataset_version="1.0", evaluator_model="qwen2.5:3b")
    db_session.add(run)
    db_session.commit()
    
    svc = EvaluationService(db_session)
    svc.load_dataset = MagicMock(return_value={"version": "1.0", "cases": [{"id": "Test-F", "category": "in_domain", "query": "Valid test query", "expected_behavior": "safe_refusal", "corpus_support": "unavailable"}]})
    
    mock_orch = MagicMock()
    mock_res = MagicMock()
    mock_res.shared_context.final_response.direct_answer = "Factual answer"
    cit = MagicMock()
    cit.source_document = "Invented"
    cit.page_number = 1
    mock_res.shared_context.final_response.citations = [cit]
    mock_res.shared_context.final_response.warnings = []
    mock_res.shared_context.final_response.metadata.confidence = 0.95
    mock_orch.orchestrate.return_value = mock_res
    svc._create_isolated_orchestrator = MagicMock(return_value=mock_orch)
    
    svc._call_ollama_evaluator = MagicMock(return_value={"success": True, "data": {"pass": False}, "raw": "", "latency": 1.0})
    
    from unittest.mock import patch
    from backend.app.services.guardrail_service import GuardrailService
    with patch.object(GuardrailService, "check_input", return_value=(True, "")), \
         patch.object(GuardrailService, "check_output", return_value=(True, "")):
        svc.run_evaluation_background("test-run-7", test_db=db_session)
    res = db_session.query(EvaluationCaseResult).filter_by(case_id="Test-F").first()
    assert res.passed is False

def test_G_unknown_system_refuses(db_session):
    run = EvaluationRun(id="test-run-8", dataset_version="1.0", evaluator_model="qwen2.5:3b")
    db_session.add(run)
    db_session.commit()
    
    svc = EvaluationService(db_session)
    svc.load_dataset = MagicMock(return_value={"version": "1.0", "cases": [{"id": "Test-G", "category": "in_domain", "query": "Q", "expected_behavior": "E", "corpus_support": "unknown"}]})
    
    mock_orch = MagicMock()
    mock_res = MagicMock()
    mock_res.shared_context.final_response.direct_answer = "I could not find related evidence"
    mock_res.shared_context.final_response.citations = []
    mock_res.shared_context.final_response.warnings = []
    mock_orch.orchestrate.return_value = mock_res
    svc._create_isolated_orchestrator = MagicMock(return_value=mock_orch)
    
    # Let judge fail it due to mismatch with expected behavior "E"
    svc._call_ollama_evaluator = MagicMock(return_value={"success": True, "data": {"pass": False, "retrieval_score": 0.0}, "raw": "", "latency": 1.0})
    
    svc.run_evaluation_background("test-run-8", test_db=db_session)
    res = db_session.query(EvaluationCaseResult).filter_by(case_id="Test-G").first()
    # It must not automatically pass or fail solely from refusal. If judge said False, it is False.
    assert res.passed is False
    assert res.corpus_support == "unknown"

