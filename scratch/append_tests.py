
def create_mock_run(db_session, id_suffix=""):
    run = EvaluationRun(id="test-run-" + id_suffix, dataset_version="1.0", evaluator_model="qwen2.5:3b")
    db_session.add(run)
    db_session.commit()
    return run

def test_A_supported_retriever_fails_system_refuses(db_session):
    create_mock_run(db_session, "A")
    svc = EvaluationService(db_session)
    svc.load_dataset = MagicMock(return_value={"version": "1.0", "cases": [{"id": "Test-A", "category": "in_domain", "query": "Q", "expected_behavior": "E", "corpus_support": "present"}]})
    
    mock_orch = MagicMock()
    mock_res = MagicMock()
    mock_res.shared_context.final_response.direct_answer = "I could not find related evidence"
    mock_res.shared_context.final_response.citations = []
    mock_res.shared_context.final_response.warnings = []
    mock_orch.orchestrate.return_value = mock_res
    svc._create_isolated_orchestrator = MagicMock(return_value=mock_orch)
    
    svc._call_ollama_evaluator = MagicMock(return_value={"success": True, "data": {"pass": False}, "raw": "", "latency": 1.0})
    
    svc.run_evaluation_background("test-run-A", test_db=db_session)
    res = db_session.query(EvaluationCaseResult).filter_by(case_id="Test-A").first()
    assert res.passed is False

def test_B_unsupported_system_refuses(db_session):
    create_mock_run(db_session, "B")
    svc = EvaluationService(db_session)
    svc.load_dataset = MagicMock(return_value={"version": "1.0", "cases": [{"id": "Test-B", "category": "in_domain", "query": "Q", "expected_behavior": "safe_refusal", "corpus_support": "unavailable"}]})
    
    mock_orch = MagicMock()
    mock_res = MagicMock()
    mock_res.shared_context.final_response.direct_answer = "I could not find related evidence"
    mock_res.shared_context.final_response.citations = []
    mock_res.shared_context.final_response.warnings = []
    mock_orch.orchestrate.return_value = mock_res
    svc._create_isolated_orchestrator = MagicMock(return_value=mock_orch)
    
    svc._call_ollama_evaluator = MagicMock(return_value={"success": True, "data": {"pass": True}, "raw": "", "latency": 1.0})
    
    svc.run_evaluation_background("test-run-B", test_db=db_session)
    res = db_session.query(EvaluationCaseResult).filter_by(case_id="Test-B").first()
    assert res.passed is True
    assert res.retrieval_score is None
    assert res.faithfulness_score == 1.0
    assert res.citation_score is None

def test_C_unsupported_system_answers(db_session):
    create_mock_run(db_session, "C")
    svc = EvaluationService(db_session)
    svc.load_dataset = MagicMock(return_value={"version": "1.0", "cases": [{"id": "Test-C", "category": "in_domain", "query": "Q", "expected_behavior": "safe_refusal", "corpus_support": "unavailable"}]})
    
    mock_orch = MagicMock()
    mock_res = MagicMock()
    mock_res.shared_context.final_response.direct_answer = "Factual answer"
    mock_res.shared_context.final_response.citations = []
    mock_res.shared_context.final_response.warnings = []
    mock_orch.orchestrate.return_value = mock_res
    svc._create_isolated_orchestrator = MagicMock(return_value=mock_orch)
    
    svc._call_ollama_evaluator = MagicMock(return_value={"success": True, "data": {"pass": False}, "raw": "", "latency": 1.0})
    
    svc.run_evaluation_background("test-run-C", test_db=db_session)
    res = db_session.query(EvaluationCaseResult).filter_by(case_id="Test-C").first()
    assert res.passed is False

def test_D_supported_system_answers(db_session):
    create_mock_run(db_session, "D")
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
    
    svc.run_evaluation_background("test-run-D", test_db=db_session)
    res = db_session.query(EvaluationCaseResult).filter_by(case_id="Test-D").first()
    assert res.passed is True
    assert res.retrieval_score == 1.0

def test_E_supported_system_answers_incorrectly(db_session):
    create_mock_run(db_session, "E")
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
    
    svc.run_evaluation_background("test-run-E", test_db=db_session)
    res = db_session.query(EvaluationCaseResult).filter_by(case_id="Test-E").first()
    assert res.passed is False

def test_F_unsupported_system_invents_citation(db_session):
    create_mock_run(db_session, "F")
    svc = EvaluationService(db_session)
    svc.load_dataset = MagicMock(return_value={"version": "1.0", "cases": [{"id": "Test-F", "category": "in_domain", "query": "Q", "expected_behavior": "safe_refusal", "corpus_support": "unavailable"}]})
    
    mock_orch = MagicMock()
    mock_res = MagicMock()
    mock_res.shared_context.final_response.direct_answer = "Factual answer"
    cit = MagicMock()
    cit.source_document = "Invented"
    cit.page_number = 1
    mock_res.shared_context.final_response.citations = [cit]
    mock_res.shared_context.final_response.warnings = []
    mock_orch.orchestrate.return_value = mock_res
    svc._create_isolated_orchestrator = MagicMock(return_value=mock_orch)
    
    svc._call_ollama_evaluator = MagicMock(return_value={"success": True, "data": {"pass": False}, "raw": "", "latency": 1.0})
    
    svc.run_evaluation_background("test-run-F", test_db=db_session)
    res = db_session.query(EvaluationCaseResult).filter_by(case_id="Test-F").first()
    assert res.passed is False

def test_G_unknown_system_refuses(db_session):
    create_mock_run(db_session, "G")
    svc = EvaluationService(db_session)
    svc.load_dataset = MagicMock(return_value={"version": "1.0", "cases": [{"id": "Test-G", "category": "in_domain", "query": "Q", "expected_behavior": "E", "corpus_support": "unknown"}]})
    
    mock_orch = MagicMock()
    mock_res = MagicMock()
    mock_res.shared_context.final_response.direct_answer = "I could not find related evidence"
    mock_res.shared_context.final_response.citations = []
    mock_res.shared_context.final_response.warnings = []
    mock_orch.orchestrate.return_value = mock_res
    svc._create_isolated_orchestrator = MagicMock(return_value=mock_orch)
    
    svc._call_ollama_evaluator = MagicMock(return_value={"success": True, "data": {"pass": False, "retrieval_score": 0.0}, "raw": "", "latency": 1.0})
    
    svc.run_evaluation_background("test-run-G", test_db=db_session)
    res = db_session.query(EvaluationCaseResult).filter_by(case_id="Test-G").first()
    assert res.passed is False
    assert res.corpus_support == "unknown"
